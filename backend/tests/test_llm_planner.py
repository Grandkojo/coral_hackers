from unittest.mock import MagicMock, patch

from app.clients.openai_client import LLMClientError
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.llm_planner_service import LLMPlannerService
from app.services.planner_service import PlannerService
from app.services.template_planner_service import TemplatePlannerService


def test_template_planner_uses_iteration_index() -> None:
    planner = TemplatePlannerService()
    state = InvestigationState(
        investigation_id="test",
        trigger_context={"github_owner": "acme", "github_repo": "svc"},
    )

    plan0 = planner.plan_next_query(state, "checkout errors")
    state.iteration_count = 1
    plan1 = planner.plan_next_query(state, "checkout errors")

    assert "coral.tables" in plan0.sql.lower()
    assert "github.pulls" in plan1.sql.lower()


def test_planner_facade_uses_template_without_api_key() -> None:
    with patch("app.services.planner_service.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        planner = PlannerService()
        assert planner.mode == "template"

        state = InvestigationState(investigation_id="test")
        plan = planner.plan_next_query(state, "Why did checkout fail?")
        assert "coral.tables" in plan.sql.lower()


def test_llm_planner_falls_back_on_error() -> None:
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.side_effect = LLMClientError("boom")

    template = TemplatePlannerService()
    planner = LLMPlannerService(llm_client=llm, template_planner=template)

    state = InvestigationState(
        investigation_id="test",
        iteration_count=1,
        trigger_context={"github_owner": "acme", "github_repo": "svc"},
    )
    plan = planner.plan_next_query(state, "checkout 500s after deploy")

    assert "github.pulls" in plan.sql.lower()
    llm.complete_json.assert_called_once()


def test_llm_planner_returns_model_sql() -> None:
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.return_value = {
        "sql": "SELECT id, title FROM sentry.issues WHERE level = 'fatal' LIMIT 10",
        "rationale": "Find fatal Sentry issues tied to the incident.",
    }

    template = TemplatePlannerService()
    planner = LLMPlannerService(llm_client=llm, template_planner=template)

    state = InvestigationState(
        investigation_id="test",
        iteration_count=2,
        trigger_context={"sentry_issue_id": "123"},
    )
    plan = planner.plan_next_query(state, "python-fastapi errors after deploy")

    assert "sentry.issues" in plan.sql
    assert plan.rationale.startswith("Find fatal")
    assert plan.iteration == 2


def test_llm_planner_iteration_zero_uses_template() -> None:
    llm = MagicMock()
    llm.enabled = True

    template = TemplatePlannerService()
    planner = LLMPlannerService(llm_client=llm, template_planner=template)

    state = InvestigationState(investigation_id="test", iteration_count=0)
    plan = planner.plan_next_query(state, "checkout errors")

    assert "coral.tables" in plan.sql.lower()
    llm.complete_json.assert_not_called()
