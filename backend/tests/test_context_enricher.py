from unittest.mock import MagicMock

from app.services.context_enricher import ContextEnricher


def test_enrich_skips_when_github_target_already_set() -> None:
    executor = MagicMock()
    enricher = ContextEnricher(query_executor=executor)

    result = enricher.enrich(
        {
            "github_owner": "acme",
            "github_repo": "checkout-service",
            "vercel_deployment_id": "dpl_abc123",
        }
    )

    assert result["github_owner"] == "acme"
    assert result["github_repo"] == "checkout-service"
    executor.execute.assert_not_called()


def test_enrich_resolves_github_from_vercel_deployment() -> None:
    executor = MagicMock()
    executor.execute.return_value = [
        {"github_owner": "Grandkojo", "github_repo": "coral_hackers"}
    ]
    enricher = ContextEnricher(query_executor=executor)

    result = enricher.enrich({"vercel_deployment_id": "dpl_abc123"})

    assert result["github_owner"] == "Grandkojo"
    assert result["github_repo"] == "coral_hackers"
    executor.execute.assert_called_once()
    assert "dpl_abc123" in executor.execute.call_args.args[0]


def test_enrich_returns_original_context_when_query_fails() -> None:
    from app.services.query_executor import QueryExecutionError

    executor = MagicMock()
    executor.execute.side_effect = QueryExecutionError("boom")
    enricher = ContextEnricher(query_executor=executor)

    context = {"vercel_deployment_id": "dpl_abc123"}
    result = enricher.enrich(context)

    assert result == context
