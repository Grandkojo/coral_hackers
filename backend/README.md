# Reef — Backend (Incident Intelligence Agent)

FastAPI service for [Pirates of the Coral-bean](https://www.wemakedevs.org/hackathons/coral) (Track 1 — Enterprise Agent).  
Architecture: `docs/architecture_diagram.txt` · Project structure: `docs/backend_project_structure.md`

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | ≥ 3.11 | |
| Coral CLI | latest | Only needed when `CORAL_MODE=cli` — see below |

---

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health`

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Reef` | Displayed in FastAPI docs |
| `APP_ENV` | `development` | |
| `DATABASE_URL` | `sqlite:///./reef.db` | SQLite for dev; swap for Postgres |
| `CORAL_MODE` | `mock` | `mock` — canned demo data · `cli` — real `coral sql` subprocess |
| `CORAL_BINARY` | `coral` | Path to the Coral binary (when `CORAL_MODE=cli`) |
| `CORAL_SQL_TIMEOUT` | `30` | Seconds before a Coral query times out |
| `MAX_INVESTIGATION_ITERATIONS` | `5` | Max orchestrator loop iterations |
| `CONFIDENCE_THRESHOLD` | `0.6` | Judge: minimum confidence to stop the loop |
| `SEVERITY_THRESHOLD` | `0.7` | Gate: above this → `human_agent_paired` |
| `GITHUB_TOKEN` | _(empty)_ | Remediation path only |
| `VERCEL_TOKEN` | _(empty)_ | Remediation path only |
| `SENTRY_TOKEN` | _(empty)_ | Remediation path only |
| `SLACK_BOT_TOKEN` | _(empty)_ | Slack notifications + approval gate |
| `SLACK_SIGNING_SECRET` | _(empty)_ | Slack slash-command verification |
| `OPENAI_API_KEY` | _(empty)_ | Phase 4B LLM planner (leave empty for template planner) |

---

## Coral setup (when `CORAL_MODE=cli`)

```bash
brew install withcoral/tap/coral
coral source add github
coral source add sentry
coral source add slack
# coral source add vercel  (community spec)
coral sql "SELECT * FROM coral.tables LIMIT 20"
```

See [Coral docs](https://withcoral.com/docs) for source configuration and MCP setup.

---

## API reference

### Trigger endpoints

#### `POST /api/v1/triggers/dashboard`

Start an investigation from the dashboard UI.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"source": "dashboard", "query": "Why did checkout fail after the last deploy?"}'
```

Response (`ReportResponse`):

```json
{
  "investigation_id": "3f4a...",
  "root_cause": "PR #234 'feat: refactor checkout payment validation' by diana.reyes may have introduced: TypeError: Cannot read properties of undefined (reading 'amount')",
  "timeline": ["Iteration 1: ...", "Root cause identified: ..."],
  "suspects": ["PR #234 ..."],
  "citations": ["coral://query-run/1", "coral://query-run/2"],
  "unresolved_gaps": [],
  "severity_score": 0.873,
  "remediation_mode": "human_agent_paired"
}
```

Also available: `POST /api/v1/triggers/slack` · `POST /api/v1/triggers/webhook`

---

### Investigation endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/investigations/{id}` | Poll status + confidence (live during loop) |
| `GET` | `/api/v1/investigations/{id}/report` | Retrieve finalized report |
| `POST` | `/api/v1/investigations/{id}/approve` | Human approval for `human_agent_paired` mode |

#### Poll status

```bash
curl http://127.0.0.1:8000/api/v1/investigations/3f4a...
```

```json
{
  "investigation_id": "3f4a...",
  "status": "complete",
  "iteration_count": 2,
  "confidence_score": 0.75,
  "root_cause": "PR #234 ...",
  "severity_score": 0.873,
  "remediation_mode": "human_agent_paired"
}
```

#### Approve remediation

```bash
curl -X POST http://127.0.0.1:8000/api/v1/investigations/3f4a.../approve
```

---

### Health

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}
```

---

## Run tests

```bash
cd backend
pytest -v
```

---

## Investigation flow (aligned with `docs/architecture_diagram.txt`)

```
Trigger API
    └─► Orchestrator loop (max 5 iterations)
            ├─► PlannerService  → QueryPlan (SQL + rationale)
            ├─► QueryExecutor   → Coral CLI/mock → rows
            ├─► EvidenceStore   → persist query run (coral://query-run/{id})
            └─► JudgeService    → update confidence + hypotheses
                                  stop when confidence ≥ 0.6 + strong hypothesis
        └─► EscalationEngine   → flag missing ownership / conflicts
        └─► SeverityGate       → score (base + blast_radius + fatal_penalty + ownership_gap)
                                  ≤ 0.7 → autonomous_fix
                                  > 0.7 → human_agent_paired
        └─► ReportGenerator    → ReportResponse + markdown
        └─► EvidenceStore      → finalize (ReportSnapshot saved to DB)
```

**Coral is the read path.** All investigation data flows through Coral SQL.  
`SlackClient` and other direct clients are used **only for remediation actions** (notifications, approval requests).
