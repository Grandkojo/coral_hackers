from unittest.mock import MagicMock, patch

from app.clients.llm_client import LLMClientError
from app.clients.llm_json import parse_json_content
from app.core.config import LlmProvider
from app.schemas.investigation import InvestigationState, QueryPlan
from app.services.llm_planner_service import LLMPlannerService
from app.services.planner_service import PlannerService
from app.services.template_planner_service import TemplatePlannerService


def test_template_planner_uses_iteration_index() -> None:
    planner = TemplatePlannerService()
    state = InvestigationState(investigation_id="test", trigger_context={})

    plan0 = planner.plan_next_query(state, "checkout errors")
    state.iteration_count = 1
    state.trigger_context = {"github_owner": "acme", "github_repo": "svc"}
    plan1 = planner.plan_next_query(state, "checkout errors")

    assert "coral.tables" in plan0.sql.lower()
    assert "github.pulls" in plan1.sql.lower()


def test_planner_facade_uses_template_without_api_key() -> None:
    with patch("app.services.planner_service.create_llm_client", return_value=None):
        planner = PlannerService()
        assert planner.mode == "template"

        state = InvestigationState(investigation_id="test")
        plan = planner.plan_next_query(state, "Why did checkout fail?")
        assert "coral.tables" in plan.sql.lower()


def test_planner_facade_uses_gemini_when_configured() -> None:
    llm = MagicMock()
    llm.enabled = True
    with (
        patch("app.services.planner_service.create_llm_client", return_value=llm),
        patch("app.services.planner_service.settings") as mock_settings,
    ):
        mock_settings.resolved_planner_llm_provider.return_value = LlmProvider.gemini
        planner = PlannerService()
        assert planner.mode == "llm:gemini"


def test_parse_json_content_strips_markdown_fence() -> None:
    parsed = parse_json_content('```json\n{"sql": "SELECT 1", "rationale": "ok"}\n```')
    assert parsed["sql"] == "SELECT 1"


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
        trigger_context={},
        last_query_row_count=3,
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
