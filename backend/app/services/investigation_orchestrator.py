from uuid import uuid4

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.investigation import InvestigationState, InvestigationStatus
from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.escalation_engine import EscalationEngine
from app.services.evidence_store import EvidenceStore
from app.services.judge_service import JudgeService
from app.services.planner_service import PlannerService
from app.services.query_executor import QueryExecutionError, QueryExecutor
from app.services.report_generator import ReportGenerator
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

    def __init__(self, evidence_store: EvidenceStore) -> None:
        self.planner = PlannerService()
        self.judge = JudgeService()
        self.query_executor = QueryExecutor()
        self.evidence_store = evidence_store
        self.escalation_engine = EscalationEngine()
        self.severity_gate = SeverityGate()
        self.report_generator = ReportGenerator()

    def run(self, trigger: TriggerRequest) -> ReportResponse:
        state = InvestigationState(investigation_id=str(uuid4()))
        self.evidence_store.create(
            state, source=trigger.source, user_query=trigger.query
        )
        logger.info(
            "investigation started id=%s source=%s",
            state.investigation_id,
            trigger.source,
        )

        citations: list[str] = []

        for _ in range(settings.max_investigation_iterations):
            plan = self.planner.plan_next_query(
                state=state, user_query=trigger.query
            )
            logger.debug(
                "iter=%d rationale=%s", state.iteration_count, plan.rationale
            )

            try:
                rows = self.query_executor.execute(plan.sql)
            except QueryExecutionError as exc:
                logger.warning(
                    "query failed at iter=%d: %s", state.iteration_count, exc
                )
                rows = []

            state.query_plans.append(plan)
            state.evidence_rows.extend(rows)
            self.judge.update_state(state, rows)

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
                    "judge: sufficient evidence at iter=%d root_cause=%s",
                    state.iteration_count,
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
