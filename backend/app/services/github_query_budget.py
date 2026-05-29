"""Guardrails for Coral SQL that hits the GitHub REST API."""

from __future__ import annotations

import re

# Authenticated PAT: 5,000 requests/hour for github.com (classic + fine-grained).
# Coral may issue multiple REST calls per SQL row; cap queries per investigation.
DEFAULT_MAX_GITHUB_QUERIES_PER_INVESTIGATION = 2

_GITHUB_DATA_PATTERN = re.compile(
    r"\b(from|join)\s+github\.",
    re.IGNORECASE,
)
_RATE_LIMIT_PATTERN = re.compile(
    r"rate\s*limit|429|too many requests",
    re.IGNORECASE,
)


def touches_github_data(sql: str) -> bool:
    """True when SQL reads GitHub source tables (triggers upstream API)."""
    return bool(_GITHUB_DATA_PATTERN.search(sql))


def is_github_rate_limit_error(message: str) -> bool:
    return bool(_RATE_LIMIT_PATTERN.search(message))


def github_rate_limited_from_context(context: dict[str, str]) -> bool:
    return context.get("github_rate_limited", "").lower() in {"1", "true", "yes"}
