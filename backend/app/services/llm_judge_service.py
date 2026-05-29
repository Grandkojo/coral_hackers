import json

from app.clients.llm_client import LLMClientError, PlannerLLMClient
from app.clients.llm_factory import create_llm_client
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.investigation import Hypothesis, InvestigationState
from app.services.rules_judge_service import (
    RulesJudgeService,
    _extract_hypotheses,
    resolve_display_root_cause,
)

logger = get_logger(__name__)

_JUDGE_SYSTEM = """
You are an incident investigation judge for a production outage.
Given new SQL evidence rows and investigation state, output JSON only:
{
  "confidence_delta": <float 0.0-0.4>,
  "hypotheses": [
    {"text": "<concise hypothesis>", "confidence": <0.0-1.0>, "source_refs": ["sentry://...", "github://pr/N"]}
  ],
  "sufficient_evidence": <boolean>,
  "root_cause": <string or null>
}
Rules:
- confidence_delta reflects how much this batch of rows increases certainty.
- Add 0-3 hypotheses grounded in the rows (PR + Sentry correlation preferred).
- sufficient_evidence true only when a credible deploy/PR/error link exists.
- root_cause: one plain-English sentence when sufficient, else null. MUST:
  * Describe the exception in readable terms (TypeError, ValueError, 401 auth, etc.).
  * Name the service/repo and pr_author when known — NO raw Sentry issue ids,
    deployment ids (dpl_…), or ISO timestamps in root_cause (those stay in SQL evidence).
  * If merged_at is after first_seen, say the PR merged after errors started and
    deploy/configuration is the likely trigger.
  * Write for an on-call engineer scanning the report, not a log parser.
"""

_MAX_ROWS = 12


class LLMJudgeService:
    """Claude/OpenAI judge: scores evidence and decides when to stop the loop."""

    def __init__(
        self,
        llm_client: PlannerLLMClient | None = None,
        rules_judge: RulesJudgeService | None = None,
    ) -> None:
        self._llm = llm_client or create_llm_client(
            settings.resolved_judge_model(),
            role="judge",
        )
        self._rules = rules_judge or RulesJudgeService()
        self._sufficient = False
        self._root_cause: str | None = None

    @property
    def enabled(self) -> bool:
        return self._llm is not None and self._llm.enabled

    def update_state(
        self,
        state: InvestigationState,
        rows: list[dict],
        user_query: str = "",
    ) -> None:
        if not self.enabled or self._llm is None:
            self._rules.update_state(state, rows)
            self._sufficient = self._rules.has_sufficient_evidence(state)
            self._root_cause = self._rules.determine_root_cause(state)
            return

        try:
            payload = self._llm.complete_json(
                system_prompt=_JUDGE_SYSTEM,
                user_prompt=_build_user_prompt(state, rows, user_query),
            )
            self._apply_payload(state, rows, payload)
        except LLMClientError as exc:
            logger.warning(
                "llm judge fallback at iter=%d: %s",
                state.iteration_count,
                exc,
            )
            self._rules.update_state(state, rows)
            self._sufficient = self._rules.has_sufficient_evidence(state)
            self._root_cause = self._rules.determine_root_cause(state)

    def has_sufficient_evidence(self, state: InvestigationState) -> bool:
        if self._sufficient:
            return True
        return self._rules.has_sufficient_evidence(state)

    def determine_root_cause(self, state: InvestigationState) -> str | None:
        resolved = resolve_display_root_cause(state, self._root_cause)
        if resolved:
            return resolved
        return self._rules.determine_root_cause(state)

    def _apply_payload(
        self,
        state: InvestigationState,
        rows: list[dict],
        payload: dict,
    ) -> None:
        delta = float(payload.get("confidence_delta", 0.0))
        delta = max(0.0, min(delta, 0.4))
        state.confidence_score = round(min(1.0, state.confidence_score + delta), 3)

        added = 0
        for item in payload.get("hypotheses") or []:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            try:
                conf = float(item.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            conf = max(0.0, min(conf, 1.0))
            refs = item.get("source_refs") or []
            if not isinstance(refs, list):
                refs = []
            state.hypotheses.append(
                Hypothesis(
                    text=text,
                    confidence=conf,
                    source_refs=[str(r) for r in refs[:8]],
                )
            )
            added += 1

        if added == 0 and rows:
            state.hypotheses.extend(
                _extract_hypotheses(rows, state.iteration_count)
            )

        self._sufficient = bool(payload.get("sufficient_evidence"))
        root = payload.get("root_cause")
        llm_root = str(root).strip() if root else None
        self._root_cause = resolve_display_root_cause(state, llm_root)
        if self._sufficient and not self._root_cause:
            self._root_cause = self._rules.determine_root_cause(state)


def _build_user_prompt(
    state: InvestigationState,
    rows: list[dict],
    user_query: str,
) -> str:
    latest_plan = state.query_plans[-1] if state.query_plans else None
    return json.dumps(
        {
            "user_query": user_query,
            "iteration": state.iteration_count,
            "confidence_threshold": settings.confidence_threshold,
            "current_confidence": state.confidence_score,
            "trigger_context": state.trigger_context,
            "latest_sql_rationale": latest_plan.rationale if latest_plan else "",
            "new_rows": rows[:_MAX_ROWS],
            "prior_hypotheses": [
                {"text": h.text, "confidence": h.confidence}
                for h in state.hypotheses[-5:]
            ],
            "total_evidence_rows": len(state.evidence_rows),
        },
        indent=2,
        default=str,
    )
