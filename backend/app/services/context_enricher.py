from app.core.logging import get_logger
from app.services.query_executor import QueryExecutionError, QueryExecutor

logger = get_logger(__name__)


class ContextEnricher:
    """Derive investigation context from Coral queries (e.g. GitHub repo from Vercel)."""

    def __init__(self, query_executor: QueryExecutor | None = None) -> None:
        self._executor = query_executor or QueryExecutor()

    def enrich(self, context: dict[str, str]) -> dict[str, str]:
        enriched = dict(context)
        if enriched.get("github_owner") and enriched.get("github_repo"):
            return enriched

        deployment_id = enriched.get("vercel_deployment_id")
        if not deployment_id:
            return enriched

        sql = f"""SELECT
  json_get_str(p.link, 'org')  AS github_owner,
  json_get_str(p.link, 'repo') AS github_repo
FROM vercel.deployments d
JOIN vercel.projects p ON p.id = d.project_id
WHERE d.uid = '{deployment_id}'
LIMIT 1"""

        try:
            rows = self._executor.execute(sql)
        except QueryExecutionError as exc:
            logger.warning("context enrich failed for %s: %s", deployment_id, exc)
            return enriched

        if not rows:
            return enriched

        row = rows[0]
        owner = row.get("github_owner")
        repo = row.get("github_repo")
        if owner:
            enriched["github_owner"] = str(owner)
        if repo:
            enriched["github_repo"] = str(repo)

        logger.info(
            "resolved github target from vercel deployment %s: %s/%s",
            deployment_id,
            enriched.get("github_owner"),
            enriched.get("github_repo"),
        )
        return enriched
