from uuid import uuid4

from app.schemas.investigation import InvestigationState
from app.schemas.report import ReportResponse
from app.schemas.trigger import TriggerRequest
from app.services.escalation_engine import EscalationEngine
from app.services.evidence_store import EvidenceStore
from app.services.judge_service import JudgeService
from app.services.planner_service import PlannerService
from app.services.query_executor import QueryExecutor
from app.services.report_generator import ReportGenerator
from app.services.severity_gate import SeverityGate


class InvestigationOrchestrator:
    """Stateful investigation loop controller."""

    def __init__(self) -> None:
        self.planner = PlannerService()
        self.judge = JudgeService()
        self.query_executor = QueryExecutor()
        self.evidence_store = EvidenceStore()
        self.escalation_engine = EscalationEngine()
        self.severity_gate = SeverityGate()
        self.report_generator = ReportGenerator()

    def run(self, trigger: TriggerRequest) -> ReportResponse:
        state = InvestigationState(investigation_id=str(uuid4()))

        for _ in range(2):
            sql = self.planner.plan_next_query(state=state, user_query=trigger.query)
            rows = self.query_executor.execute(sql)

            state.iteration_count += 1
            state.evidence_rows.extend(rows)
            state.hypotheses.append(f"Potential owner: team-platform (source={trigger.source})")
            state.confidence_score = min(1.0, state.confidence_score + 0.35)

            if self.judge.has_sufficient_evidence(state):
                state.root_cause = "Most likely recent deployment regression"
                break

        _ = self.escalation_engine.evaluate(state)
        self.evidence_store.save(state)

        severity_score = self.severity_gate.calculate_severity(state)
        remediation_mode = self.severity_gate.remediation_mode(severity_score)

        return self.report_generator.generate(
            state=state,
            severity_score=severity_score,
            remediation_mode=remediation_mode,
        )
