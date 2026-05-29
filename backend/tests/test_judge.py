from unittest.mock import MagicMock, patch

from app.clients.llm_client import LLMClientError
from app.core.config import LlmProvider
from app.schemas.investigation import InvestigationState
from app.services.judge_service import JudgeService
from app.services.llm_judge_service import LLMJudgeService
from app.services.rules_judge_service import (
    RulesJudgeService,
    build_display_root_cause,
    build_structured_root_cause,
    has_pr_error_correlation,
    is_valid_display_root_cause,
    resolve_display_root_cause,
)


def test_rules_judge_detects_pr_sentry_hypothesis() -> None:
    judge = RulesJudgeService()
    state = InvestigationState(investigation_id="t1", iteration_count=1)
    rows = [
        {
            "pr_title": "fix checkout",
            "pr_number": 12,
            "pr_author": "dev",
            "error_message": "TypeError in payment",
            "sentry_issue_id": "99",
        }
    ]
    judge.update_state(state, rows)
    assert state.confidence_score > 0
    assert any("PR #12" in h.text for h in state.hypotheses)


def test_judge_facade_uses_rules_without_api_key() -> None:
    with patch("app.services.judge_service.create_llm_client", return_value=None):
        judge = JudgeService()
        assert judge.mode == "rules"


def test_judge_facade_uses_llm_when_configured() -> None:
    llm = MagicMock()
    llm.enabled = True
    with (
        patch("app.services.judge_service.create_llm_client", return_value=llm),
        patch("app.services.judge_service.settings") as mock_settings,
    ):
        mock_settings.resolved_judge_llm_provider.return_value = LlmProvider.groq
        mock_settings.resolved_judge_model.return_value = "llama-3.3-70b-versatile"
        judge = JudgeService()
        assert judge.mode == "llm:groq"


def test_display_root_cause_avoids_raw_ids() -> None:
    rows = [
        {
            "sentry_issue_id": "123540686",
            "error_message": (
                "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"
            ),
            "first_seen": "2026-05-29T11:09:52Z",
            "deployment_id": "dpl_5oWAuYnVHi6FGSFXpB1eAL5Xd5PB",
            "deploy_at": "2026-05-29T11:09:05.113Z",
        },
        {
            "pr_number": 1,
            "pr_author": "Grandkojo",
            "merged_at": "2026-05-29T11:32:07Z",
        },
    ]
    text = build_display_root_cause(
        rows, {"github_repo": "reef-incident-lab"}
    )
    assert text is not None
    assert "Grandkojo" in text
    assert "reef-incident-lab" in text
    assert "123540686" not in text
    assert "dpl_" not in text
    assert "2026-05-29" not in text


def test_structured_root_cause_quotes_error_and_author() -> None:
    rows = [
        {
            "id": "123540686",
            "title": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
            "first_seen": "2026-05-29T11:09:52Z",
        },
        {
            "deployment_id": "dpl_5oWAuYnVHi6FGSFXpB1eAL5Xd5PB",
            "deploy_at": "2026-05-29T11:09:05.113Z",
            "sentry_issue_id": "123540686",
            "error_message": (
                "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"
            ),
        },
        {
            "pr_number": 1,
            "pr_title": "wave-2: document checkout regression demo",
            "pr_author": "Grandkojo",
            "merged_at": "2026-05-29T11:32:07Z",
            "deployment_id": "dpl_5oWAuYnVHi6FGSFXpB1eAL5Xd5PB",
            "deploy_at": "2026-05-29T11:09:05.113Z",
        },
    ]
    assert has_pr_error_correlation(rows)
    text = build_structured_root_cause(rows)
    assert text is not None
    assert "TypeError: unsupported operand" in text
    assert "Grandkojo" in text
    assert "PR #1" in text
    assert "merged after first error" in text


def test_rules_judge_prefers_display_root_cause_at_iter_3() -> None:
    judge = RulesJudgeService()
    state = InvestigationState(investigation_id="t-structured", iteration_count=4)
    state.trigger_context = {"github_repo": "reef-incident-lab"}
    state.evidence_rows = [
        {
            "sentry_issue_id": "123540686",
            "error_message": "TypeError: NoneType and int",
            "first_seen": "2026-05-29T11:09:52Z",
            "deploy_at": "2026-05-29T11:09:05Z",
            "deployment_id": "dpl_x",
        },
        {
            "pr_number": 1,
            "pr_author": "Grandkojo",
            "merged_at": "2026-05-29T11:32:07Z",
        },
    ]
    root = judge.determine_root_cause(state)
    assert root is not None
    assert "Grandkojo" in root
    assert "dpl_x" not in root
    assert "123540686" not in root


def test_is_valid_display_root_cause_accepts_wave3_auth_summary() -> None:
    ctx = {"error_message": "ValueError: invalid credentials schema"}
    assert is_valid_display_root_cause(
        "Production deploy to reef-incident-lab broke authentication with a "
        "ValueError on login; configuration change is the likely trigger.",
        ctx,
    )
    assert not is_valid_display_root_cause(
        "Checkout TypeError on null amount caused 500 errors after deploy.",
        ctx,
    )


def test_aggregate_ignores_pr_merged_before_deploy() -> None:
    from app.services.rules_judge_service import _aggregate_correlation_fields

    rows = [
        {
            "error_message": "ValueError: invalid credentials schema",
            "first_seen": "2026-05-29T14:13:51Z",
            "deploy_at": "2026-05-29T14:13:18Z",
            "deployment_id": "dpl_w3",
        },
        {
            "pr_number": 1,
            "pr_author": "Grandkojo",
            "merged_at": "2026-05-29T11:32:07Z",
            "deploy_at": "2026-05-29T14:13:18Z",
        },
    ]
    ctx = _aggregate_correlation_fields(rows)
    assert "pr_number" not in ctx
    assert ctx["error_message"].startswith("ValueError")


def test_display_root_cause_deploy_only_when_pr_predates_deploy() -> None:
    rows = [
        {
            "error_message": "ValueError: invalid credentials schema",
            "first_seen": "2026-05-29T14:13:51Z",
            "deploy_at": "2026-05-29T14:13:18Z",
            "deployment_id": "dpl_w3",
        },
    ]
    text = build_display_root_cause(rows, {"github_repo": "reef-incident-lab"})
    assert text is not None
    assert "Grandkojo" not in text
    assert "PR" not in text
    assert "deploy" in text.lower()


def test_llm_root_rejected_when_mentions_pr_without_evidence() -> None:
    ctx = {
        "error_message": "ValueError: invalid credentials schema",
        "first_seen": "2026-05-29T14:13:51Z",
    }
    assert not is_valid_display_root_cause(
        "ValueError on login caused by PR #1 from Grandkojo after deploy.",
        ctx,
    )


def test_summarize_exception_wave3_valueerror() -> None:
    from app.services.rules_judge_service import _summarize_exception

    text = _summarize_exception("ValueError: invalid credentials schema")
    assert "authentication" in text.lower() or "ValueError" in text


def test_is_valid_display_root_cause_rejects_ids_and_500_only() -> None:
    ctx = {"error_message": "TypeError: NoneType and int"}
    assert not is_valid_display_root_cause(
        "Checkout returned 500 errors after deploy dpl_abc.", ctx
    )
    assert not is_valid_display_root_cause(
        "Issue 123540686 failed after 2026-05-29T11:09:05Z", ctx
    )
    assert is_valid_display_root_cause(
        "Production deploy to reef-incident-lab exposed a checkout TypeError "
        "when amount is null; PR by Grandkojo merged after errors started.",
        ctx,
    )


def test_llm_judge_uses_valid_llm_root_cause() -> None:
    llm_root = (
        "Production deploy to reef-incident-lab exposed a checkout TypeError "
        "when a null amount is added; pull request by Grandkojo merged after "
        "errors started, so configuration change is the likely trigger."
    )
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.return_value = {
        "confidence_delta": 0.2,
        "hypotheses": [],
        "sufficient_evidence": True,
        "root_cause": llm_root,
    }
    judge = LLMJudgeService(llm_client=llm)
    state = InvestigationState(investigation_id="t4", iteration_count=4)
    state.evidence_rows = [
        {
            "error_message": "TypeError: NoneType and int",
            "first_seen": "2026-05-29T11:09:52Z",
            "deployment_id": "dpl_1",
            "deploy_at": "2026-05-29T11:09:05Z",
        },
        {
            "pr_number": 2,
            "pr_author": "Grandkojo",
            "merged_at": "2026-05-29T11:32:07Z",
        },
    ]
    state.trigger_context = {"github_repo": "reef-incident-lab"}
    judge.update_state(state, [], user_query="500 errors on checkout")
    assert judge.determine_root_cause(state) == llm_root


def test_llm_judge_falls_back_when_llm_root_invalid() -> None:
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.return_value = {
        "confidence_delta": 0.2,
        "hypotheses": [],
        "sufficient_evidence": True,
        "root_cause": "Checkout returned 500 errors after deploy.",
    }
    judge = LLMJudgeService(llm_client=llm)
    state = InvestigationState(investigation_id="t4b", iteration_count=4)
    state.evidence_rows = [
        {
            "error_message": "TypeError: bad add",
            "first_seen": "2026-05-29T11:09:52Z",
            "sentry_issue_id": "99",
            "deployment_id": "dpl_1",
            "deploy_at": "2026-05-29T11:09:05Z",
        },
        {
            "pr_number": 2,
            "pr_author": "dev",
            "merged_at": "2026-05-29T11:32:07Z",
        },
    ]
    state.trigger_context = {"github_repo": "reef-incident-lab"}
    judge.update_state(state, [], user_query="500 errors on checkout")
    root = judge.determine_root_cause(state)
    assert root is not None
    assert "dev" in root
    assert "dpl_1" not in root
    assert root != "Checkout returned 500 errors after deploy."


def test_resolve_display_root_cause_prefers_llm_when_valid() -> None:
    state = InvestigationState(investigation_id="t5", iteration_count=4)
    state.evidence_rows = [
        {"error_message": "TypeError: x", "deployment_id": "dpl_z"},
        {"pr_number": 1, "pr_author": "alice"},
    ]
    llm = "Deploy to api exposed a TypeError in checkout after go-live."
    assert resolve_display_root_cause(state, llm) == llm


def test_llm_judge_applies_payload() -> None:
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.return_value = {
        "confidence_delta": 0.2,
        "hypotheses": [
            {
                "text": "Deploy dpl_abc caused fatal errors",
                "confidence": 0.8,
                "source_refs": ["sentry://1", "github://pr/5"],
            }
        ],
        "sufficient_evidence": True,
        "root_cause": "PR #5 introduced regression",
    }

    judge = LLMJudgeService(llm_client=llm)
    state = InvestigationState(investigation_id="t2", iteration_count=1)
    judge.update_state(state, [{"pr_number": 5}], user_query="checkout failed")

    assert state.confidence_score == 0.2
    assert judge.has_sufficient_evidence(state)
    assert judge.determine_root_cause(state) == "PR #5 introduced regression"


def test_llm_judge_falls_back_on_error() -> None:
    llm = MagicMock()
    llm.enabled = True
    llm.complete_json.side_effect = LLMClientError("rate limit")

    rules = RulesJudgeService()
    judge = LLMJudgeService(llm_client=llm, rules_judge=rules)
    state = InvestigationState(investigation_id="t3", iteration_count=1)
    rows = [
        {
            "pr_title": "fix",
            "pr_number": 1,
            "pr_author": "a",
            "error_message": "err",
            "sentry_issue_id": "1",
        }
    ]
    judge.update_state(state, rows, user_query="incident")

    assert any("PR #1" in h.text for h in state.hypotheses)
