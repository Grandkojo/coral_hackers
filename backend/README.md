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
| `GITHUB_TOKEN` | _(empty)_ | Coral github source + Reef remediation |
| `GITHUB_OWNER` | _(empty)_ | Coral `github.pulls` / ownership filters |
| `GITHUB_REPO` | _(empty)_ | Coral `github.pulls` / ownership filters |
| `GITHUB_ACCOUNT_TYPE` | `user` | `user` → `github.collaborators` · `org` → `github.teams` |
| `VERCEL_TOKEN` | _(empty)_ | Remediation path only |
| `SENTRY_TOKEN` | _(empty)_ | Remediation path only |
| `SLACK_BOT_TOKEN` | _(empty)_ | Slack notifications + approval gate |
| `SLACK_SIGNING_SECRET` | _(empty)_ | Slack slash-command verification |
| `PLANNER_LLM_PROVIDER` | `gemini` | `gemini` or `groq` for SQL planning |
| `JUDGE_LLM_PROVIDER` | `groq` | `groq` (fast) or `gemini` for evidence judging |
| `GEMINI_API_KEY` | _(empty)_ | Free — [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | _(empty)_ | Free — [console.groq.com](https://console.groq.com/keys) |
| `PLANNER_MODEL` | `gemini-2.5-flash` | Override planner model id |
| `JUDGE_MODEL` | `llama-3.3-70b-versatile` | Override judge model id |

---

## Coral setup (when `CORAL_MODE=cli`)

Credential template: `backend/.env.example` (shared tokens + Coral-specific keys like `SENTRY_ORG` and `SLACK_TOKEN`).

Non-interactive setup for enterprises (env vars → Coral sources):

```bash
brew install withcoral/tap/coral   # or install to ~/.local/bin
cp .env.example .env               # fill GITHUB_TOKEN, SENTRY_ORG, SENTRY_TOKEN, SLACK_TOKEN
set -a && source .env && set +a
./scripts/setup_coral_sources.sh
```

Then set `CORAL_MODE=cli` in `.env` and restart the API.

Manual alternative:

```bash
coral source add github   # reads GITHUB_TOKEN from env
coral source add sentry   # reads SENTRY_ORG, SENTRY_TOKEN
coral source add slack    # reads SLACK_TOKEN
coral sql "SELECT schema_name, table_name FROM coral.tables LIMIT 20"
```

## Simulate triggers (demo / hackathon)

With the API running (`uvicorn app.main:app --reload`) and Coral configured:

```bash
# 8 dashboard scenarios (4 NL + 4 Vercel URL) + 4 Sentry webhooks
./scripts/simulate_triggers.sh all

# Subsets
./scripts/simulate_triggers.sh dashboard
./scripts/simulate_triggers.sh sentry
```

**Sentry webhook URL** (configure in Sentry → Settings → Developer Settings → Internal Integrations):

```
POST http://YOUR_HOST/api/v1/webhooks/sentry
```

**Dashboard** accepts NL query and/or Vercel deployment URL:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"vercel_url":"dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"}'
```

See `scripts/fixtures/` for sample payloads.

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

## Deploy on GCE (Docker + Postgres + Coral CLI)

Production guide: [`deploy/gce/README.md`](../deploy/gce/README.md)

Quick local smoke test with the same stack:

```bash
cd backend
cp ../deploy/gce/env.production.example .env   # edit tokens
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

---

## Investigation flow (aligned with `docs/architecture_diagram.txt`)

```
Trigger API
    └─► Orchestrator loop (max 5 iterations)
            ├─► PlannerService  → QueryPlan (SQL + rationale)
            ├─► QueryExecutor   → Coral CLI/mock → rows
            ├─► EvidenceStore   → persist query run (coral://query-run/{id})
            └─► JudgeService    → Groq/Gemini LLM or rules: confidence + hypotheses
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
