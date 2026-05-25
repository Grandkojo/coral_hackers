from app.schemas.investigation import InvestigationState


class PlannerService:
    """Planner LLM: decides the next data request."""

    def plan_next_query(self, state: InvestigationState, user_query: str) -> str:
        if state.iteration_count == 0:
            return (
                "SELECT * FROM deployments, prs, incidents, logs "
                "WHERE incident_context MATCHES user_query"
            )
        return "SELECT * FROM ownership, slack_threads WHERE related_to_hypotheses = true"
