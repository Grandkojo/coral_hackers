from app.services.github_query_budget import (
    github_rate_limited_from_context,
    is_github_rate_limit_error,
    touches_github_data,
)


def test_touches_github_data_detects_pulls():
    sql = "SELECT * FROM github.pulls WHERE owner = 'o'"
    assert touches_github_data(sql) is True


def test_touches_github_data_ignores_sentry_only():
    sql = "SELECT * FROM sentry.issues LIMIT 5"
    assert touches_github_data(sql) is False


def test_is_github_rate_limit_error():
    assert is_github_rate_limit_error("API rate limit exceeded for user") is True
    assert is_github_rate_limit_error("HTTP 429 Too Many Requests") is True
    assert is_github_rate_limit_error("column not found") is False


def test_github_rate_limited_from_context():
    assert github_rate_limited_from_context({"github_rate_limited": "true"})
    assert not github_rate_limited_from_context({})
