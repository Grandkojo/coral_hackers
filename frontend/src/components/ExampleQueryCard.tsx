const EXAMPLE_SQL = `SELECT
  g.title,
  g.number       AS pr_number,
  s.title        AS error_message,
  s.level,
  s.first_seen
FROM github.pulls g
JOIN sentry.issues s
  ON s.first_seen >= g.merged_at
WHERE g.owner = 'acme'
  AND g.repo = 'checkout-service'
  AND s.level IN ('fatal', 'error')
ORDER BY s.first_seen DESC
LIMIT 20;`;

export default function ExampleQueryCard() {
  return (
    <div className="card card-hover example-query-card">
      <div className="card-header">
        <div>
          <span className="label block mb-1">Example Coral query</span>
          <span className="font-body text-sm" style={{ color: "var(--ink-2)" }}>
            Cross-source JOIN — no warehouse, no ETL
          </span>
        </div>
        <span className="feature-chip">Read-only SQL</span>
      </div>

      <div className="example-query-body">
        <pre>{EXAMPLE_SQL}</pre>
      </div>

      <div className="example-query-footer">
        <span className="feature-chip">Transparent evidence</span>
        <span className="feature-chip">Human approval gate</span>
        <span className="feature-chip">Vercel Sentry GitHub Slack</span>
      </div>
    </div>
  );
}
