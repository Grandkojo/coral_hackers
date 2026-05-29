from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.investigation import InvestigationState, InvestigationStatus
from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.context_enricher import ContextEnricher
from app.services.escalation_engine import EscalationEngine
from app.services.evidence_store import EvidenceStore
from app.services.judge_service import JudgeService
from app.services.planner_service import PlannerService
from app.services.github_query_budget import (
    github_rate_limited_from_context,
    is_github_rate_limit_error,
    touches_github_data,
)
from app.services.trigger_discovery import apply_discovered_context
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.report_generator import ReportGenerator
from app.schemas.org_context import OrgContext
from app.services.severity_gate import SeverityGate

logger = get_logger(__name__)


class InvestigationOrchestrator:
    """Stateful investigation loop controller.

    Flow (per architecture_diagram.txt):
      Trigger → Orchestrator ⇄ (Planner + Judge) → QueryExecutor → Coral
                     ↓ each iteration
               EvidenceStore
                     ↓ after loop
               EscalationEngine → SeverityGate → ReportGenerator
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        org_context: OrgContext | None = None,
    ) -> None:
        self._org_context = org_context
        self._organization_id = org_context.organization_id if org_context else None
        coral_dir = org_context.coral_config_dir if org_context else None
        self.planner = PlannerService()
        self.judge = JudgeService()
        self.query_executor = QueryExecutor(coral_config_dir=coral_dir)
        self.context_enricher = ContextEnricher(query_executor=self.query_executor)
        self.evidence_store = evidence_store
        self.escalation_engine = EscalationEngine()
        self.severity_gate = SeverityGate()
        self.report_generator = ReportGenerator()

    def _execute_planned_query(
        self, state: InvestigationState, sql: str
    ) -> list[dict]:
        """Run Coral SQL with a per-investigation GitHub API budget."""
        if touches_github_data(sql):
            if state.github_rate_limited or github_rate_limited_from_context(
                state.trigger_context
            ):
                logger.info(
                    "skipping GitHub Coral query (rate limited earlier) iter=%d",
                    state.iteration_count,
                )
                return []
            if (
                state.github_queries_executed
                >= settings.max_github_queries_per_investigation
            ):
                logger.info(
                    "skipping GitHub Coral query (budget %d) iter=%d",
                    settings.max_github_queries_per_investigation,
                    state.iteration_count,
                )
                return []

        try:
            rows = self.query_executor.execute(sql)
        except QueryExecutionError as exc:
            message = str(exc)
            if touches_github_data(sql) and is_github_rate_limit_error(message):
                state.github_rate_limited = True
                state.trigger_context["github_rate_limited"] = "true"
                logger.warning(
                    "GitHub rate limit at iter=%d — further GitHub queries skipped",
                    state.iteration_count,
                )
            else:
                logger.warning(
                    "query failed at iter=%d: %s",
                    state.iteration_count,
                    message,
                )
            return []

        if touches_github_data(sql):
            state.github_queries_executed += 1
        return rows

    def run(self, trigger: TriggerRequest) -> ReportResponse:
        self.judge.set_user_query(trigger.query or "")
        base_context = dict(trigger.context)
        if self._org_context is not None:
            base_context = self._org_context.apply_to_trigger_context(base_context)
            base_context["github_account_type"] = self._org_context.github_account_type.value
        trigger_context = self.context_enricher.enrich(base_context)
        state = InvestigationState(
            investigation_id=str(uuid4()),
            trigger_context=trigger_context,
        )
        self.evidence_store.create(
            state,
            source=trigger.source,
            user_query=trigger.query,
            organization_id=self._organization_id,
        )
        logger.info(
            "investigation started id=%s source=%s trigger_type=%s",
            state.investigation_id,
            trigger.source,
            trigger.context.get("trigger_type", "manual"),
        )

        citations: list[str] = []

        for _ in range(settings.max_investigation_iterations):
            plan = self.planner.plan_next_query(
                state=state, user_query=trigger.query
            )
            logger.debug(
                "iter=%d rationale=%s planner=%s",
                state.iteration_count,
                plan.rationale,
                self.planner.mode,
            )

            rows = self._execute_planned_query(state, plan.sql)
            state.trigger_context = apply_discovered_context(
                state.trigger_context, rows
            )

            state.query_plans.append(plan)
            state.query_row_counts.append(len(rows))
            state.last_query_row_count = len(rows)
            state.evidence_rows.extend(rows)
            self.judge.update_state(state, rows)

            logger.debug(
                "iter=%d judge=%s confidence=%.3f",
                state.iteration_count,
                self.judge.mode,
                state.confidence_score,
            )

            citation = self.evidence_store.append_query_run(
                state=state,
                sql=plan.sql,
                rationale=plan.rationale,
                rows=rows,
            )
            citations.append(citation)

            state.iteration_count += 1
            self.evidence_store.save(state)

            logger.debug(
                "iter=%d rows=%d confidence=%.3f hyps=%d",
                state.iteration_count,
                len(rows),
                state.confidence_score,
                len(state.hypotheses),
            )

            if self.judge.has_sufficient_evidence(state):
                state.root_cause = self.judge.determine_root_cause(state)
                logger.info(
                    "judge: sufficient evidence at iter=%d mode=%s root_cause=%s",
                    state.iteration_count,
                    self.judge.mode,
                    state.root_cause,
                )
                break

        state.escalation_flags = self.escalation_engine.evaluate(state)

        if not state.root_cause:
            state.root_cause = self.judge.determine_root_cause(state)

        severity_score = self.severity_gate.calculate_severity(state)
        remediation_mode = self.severity_gate.remediation_mode(severity_score)

        report, markdown = self.report_generator.generate(
            state=state,
            severity_score=severity_score,
            remediation_mode=remediation_mode,
            citations=citations,
        )

        state.status = InvestigationStatus.complete
        self.evidence_store.finalize(
            state=state,
            report=report,
            severity_score=severity_score,
            remediation_mode=remediation_mode,
            markdown=markdown,
        )

        logger.info(
            "investigation complete id=%s severity=%.2f mode=%s",
            state.investigation_id,
            severity_score,
            remediation_mode,
        )
        return report
