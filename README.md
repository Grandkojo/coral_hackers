# Reef — Production Incident Intelligence Agent

**Reef compresses hours of cross-tool incident triage into a single investigation workflow.** It correlates signals across GitHub, Sentry, Vercel, and Slack, identifies a root cause, and either remediates autonomously or brings a human into the loop based on severity.

---

## The Problem

When something breaks in production, engineers spend hours manually stitching together:

- Which PR landed just before the incident?
- Which errors surfaced in Sentry around the same time?
- What did the on-call thread in Slack say?
- Who owns the affected service?
- Did a Vercel deployment go out in that window?

The information is scattered, the timeline has to be pieced together manually, and the root cause is often found long after the impact has spread.

**Reef automates the entire investigation.**

---

## How Reef Works

Reef runs a stateful investigation loop powered by [Coral](https://withcoral.ai) — a SQL runtime that JOINs across GitHub, Sentry, Slack, and Vercel in a single query, with no ETL and no data leaving your machine.

**1. Trigger**: An incident arrives via the Reef dashboard, a Sentry webhook, or a `/reef` Slack slash command in your incident channel.

**2. Plan**: The Gemini planner LLM receives the full investigation context and decides which Coral SQL query to run next, along with a rationale.

**3. Execute**: Reef passes the query to Coral, which resolves data locally from your connected sources. Data never gets stuffed into the agent context.

**4. Judge**: The Groq judge LLM evaluates the returned evidence, scores confidence from 0.0 to 1.0, and extracts structured hypotheses about root cause.

**5. Repeat**: If confidence is below the threshold (default: 0.6), the planner generates the next query. The loop runs for up to 5 iterations.

**6. Escalate**: The escalation engine flags unresolved gaps: missing CODEOWNERS match, conflicting hypotheses, or insufficient evidence.

**7. Gate**: The severity gate applies a weighted score and decides: autonomous fix, or human approval required.

**8. Report**: Reef produces a structured report with a full timeline, suspected PRs, Coral query citations, and unresolved gaps.

Example Coral query generated during an investigation:

```sql
SELECT g.title, s.error_message, sl.text
FROM github.pull_requests g
JOIN sentry.issues s
  ON s.first_seen >= g.merged_at
JOIN slack.messages sl
  ON sl.channel = '#incidents'
WHERE s.level = 'fatal'
ORDER BY s.first_seen DESC;
```

One query. Three sources. No ETL.

---

## Platform Integrations

| Platform | Investigation role | Trigger / Remediation |
|----------|-------------------|-----------------------|
| **GitHub** | PR and commit correlation, CODEOWNERS ownership lookup | Revert PR on the suspected commit in autonomous mode |
| **Sentry** | Error correlation by timestamp, fatal error severity weighting | Webhook trigger new issue auto-starts an investigation |
| **Vercel** | Deployment timeline correlation, incident window anchoring | Rollback the identified deployment in autonomous mode |
| **Slack** | Incident thread context and on-call discussion history | `/reef` slash command trigger · Human approval gate for high-severity remediation |

**Slack and the human gate.** When severity exceeds the threshold, Reef posts a structured approval request to your incident channel. It includes the full evidence, the suspected PR, and the proposed action. One click approves or rejects.

---

## AI Models

Reef uses two LLMs in the investigation loop, each with a distinct role.

**Planner : Gemini 2.5 Flash.** Answers *what should we investigate next?* At each iteration it receives the original query, all previous results, and the hypotheses built so far, then outputs the next Coral SQL query and a plain-English rationale.

Default: `gemini-2.5-flash` via [Google AI Studio](https://aistudio.google.com/apikey) (free tier, no billing required).

**Judge : Groq / Llama 3.3 70B.** Answers *is this evidence sufficient to stop?* After each query it scores confidence (0.0–1.0) and extracts structured hypotheses. When confidence reaches 0.6 with a strong hypothesis, the loop terminates. Groq's low latency keeps the loop tight.

Default: `llama-3.3-70b-versatile` via [Groq Console](https://console.groq.com/keys) (free tier, no billing required).

Both roles accept `gemini`, `groq`, `openai`, or `anthropic`, swap with `PLANNER_LLM_PROVIDER` / `JUDGE_LLM_PROVIDER`. If no LLM keys are configured, Reef falls back to a template-based planner and a rules-based judge (row count + fatal signal detection + deployment correlation). The full loop still runs.

---

## Severity Gate and Remediation

After root cause is identified, Reef scores the incident using a weighted formula:

- Base confidence score from the judge
- Blast radius (affected user count from Sentry)
- Fatal error penalty (`+0.15` when Sentry reports `fatal` level)
- Ownership gap penalty (`+0.05` when no CODEOWNERS match is found)

| Severity Score | Mode | What Reef does |
|----------------|------|----------------|
| ≤ 0.7 | `autonomous_fix` | Reef proceeds: reverts the PR, rolls back the Vercel deployment, posts a resolution to Slack |
| > 0.7 | `human_agent_paired` | Reef posts an approval request to Slack. A human approves or rejects before anything is executed |

High-severity incidents always have a human in the loop. Low-risk incidents resolve without paging anyone.

---

## Architecture

### Backend

A **FastAPI** service (Python 3.11+) that runs the investigation loop and exposes REST endpoints for triggering, polling, reporting, and approving remediation. The core pipeline is `Orchestrator → Planner → QueryExecutor (Coral) → EvidenceStore → Judge → EscalationEngine → SeverityGate → ReportGenerator`. Each investigation and every Coral query run it executes are persisted to the database with full citations (`coral://query-run/{id}`).

**Database:** SQLAlchemy ORM. SQLite in development, PostgreSQL 16 in production. Core tables: `investigations`, `query_runs`, `report_snapshots`, and per-org multi-tenant tables with encrypted credential storage.

**Coral** runs in two modes set by `CORAL_MODE`:
- `mock`:canned demo data, no Coral install needed
- `cli` : real `coral sql` subprocesses against your connected sources

### Frontend

A **React 19 + TypeScript** app (Vite, Tailwind CSS, React Router v7) deployed on Vercel. The dashboard lets engineers trigger investigations via natural language query or Vercel deployment URL, watch the live investigation loop iteration by iteration, and read the final report with timeline, suspects, and Coral citations. State is managed via React Context; the API layer uses typed HTTP wrappers against the FastAPI backend.

---

## Getting Started

### Prerequisites

| Tool | Version | When needed |
|------|---------|-------------|
| Python | ≥ 3.11 | Backend |
| Node.js | ≥ 18 | Frontend |
| pnpm | latest | Frontend |
| Docker + Compose | latest | Docker deployment |
| Coral CLI | latest | `CORAL_MODE=cli` only |

### Local Development — SQLite + mock Coral

No external database or Coral install required.

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

```bash
# Frontend (separate terminal)
cd frontend
pnpm install
pnpm dev
```

Backend at `http://127.0.0.1:8000` · Frontend at `http://localhost:5173`

Trigger a test investigation:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"query": "Why did checkout fail after the last deploy?"}'
```

### Docker Compose — Postgres + Coral CLI

```bash
cp backend/.env.example backend/.env   # fill credentials, set CORAL_MODE=cli
docker compose -f backend/docker-compose.yml up -d --build
curl http://127.0.0.1:8000/health
```

### Coral CLI setup (when `CORAL_MODE=cli`)

```bash
brew install withcoral/tap/coral
cp backend/.env.example backend/.env   # fill GITHUB_TOKEN, SENTRY_ORG, SENTRY_TOKEN, SLACK_TOKEN
set -a && source backend/.env && set +a
./scripts/setup_coral_sources.sh       # non-interactive: reads tokens from env
```

### Production — GCE + nginx + Let's Encrypt

Full guide: [`deploy/gce/README.md`](deploy/gce/README.md) — covers VM provisioning, Docker Compose, nginx TLS, and Vercel frontend wiring.

---

## Configuration

All configuration lives in `backend/.env`. Start from `backend/.env.example`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./reef.db` | SQLite for dev · Postgres connection string for production |
| `CORAL_MODE` | `mock` | `mock` for demo data · `cli` for real Coral queries |
| `CORAL_BINARY` | `coral` | Path to the Coral CLI binary |
| `CORAL_SQL_TIMEOUT` | `30` | Seconds before a Coral query times out |
| `MAX_INVESTIGATION_ITERATIONS` | `5` | Max loop iterations per investigation |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimum confidence score to stop the loop |
| `SEVERITY_THRESHOLD` | `0.7` | Above this → `human_agent_paired` mode |

### Platform Credentials

| Variable | Used for |
|----------|---------|
| `GITHUB_TOKEN` | Coral GitHub source + PR revert |
| `GITHUB_OWNER` / `GITHUB_REPO` | Coral query filters |
| `GITHUB_ACCOUNT_TYPE` | `user` → collaborators · `org` → teams |
| `SENTRY_ORG` / `SENTRY_TOKEN` | Coral Sentry source |
| `SLACK_TOKEN` | Coral Slack reads (incident threads) |
| `SLACK_BOT_TOKEN` / `SLACK_SIGNING_SECRET` | Notifications, approval gate, slash command verification |
| `VERCEL_TOKEN` / `VERCEL_TEAM_ID` | Coral Vercel source + rollback |

### AI Models

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANNER_LLM_PROVIDER` | `gemini` | `gemini`, `groq`, `openai`, or `anthropic` |
| `JUDGE_LLM_PROVIDER` | `groq` | `groq`, `gemini`, `openai`, or `anthropic` |
| `GEMINI_API_KEY` | _(empty)_ | Free at [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | _(empty)_ | Free at [console.groq.com](https://console.groq.com/keys) |
| `PLANNER_MODEL` | `gemini-2.5-flash` | Override planner model ID |
| `JUDGE_MODEL` | `llama-3.3-70b-versatile` | Override judge model ID |

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/triggers/dashboard` | Start an investigation from the UI |
| `POST` | `/api/v1/triggers/slack` | Start from a Slack slash command |
| `POST` | `/api/v1/webhooks/sentry` | Async investigation from a Sentry webhook |
| `GET` | `/api/v1/investigations/{id}` | Poll status and live confidence |
| `GET` | `/api/v1/investigations/{id}/report` | Retrieve the finalized report |
| `POST` | `/api/v1/investigations/{id}/approve` | Approve remediation (`human_agent_paired` mode) |
| `GET` | `/health` | Liveness check |

### Response shape

```json
{
  "investigation_id": "3f4a...",
  "root_cause": "PR #234 'feat: refactor checkout payment validation' by diana.reyes may have introduced: TypeError: Cannot read properties of undefined (reading 'amount')",
  "timeline": ["Iteration 1: queried recent deployments", "Root cause identified: ..."],
  "suspects": ["PR #234 feat: refactor checkout payment validation"],
  "citations": ["coral://query-run/1", "coral://query-run/2"],
  "unresolved_gaps": [],
  "severity_score": 0.873,
  "remediation_mode": "human_agent_paired"
}
```

Swagger UI at `http://127.0.0.1:8000/docs` · Postman collection (17 requests, full lifecycle) at [`docs/reef_postman_collection.json`](docs/reef_postman_collection.json).

---

## Integrating with Your Team

**Sentry alerts → automatic investigations.** In Sentry → Settings → Developer Settings → Internal Integrations, point a webhook at `POST https://your-reef-host/api/v1/webhooks/sentry`. Every new issue kicks off an investigation automatically. Your on-call engineer gets a Slack message when the report is ready.

**Slack slash command.** Configure `/reef` to POST to `https://your-reef-host/api/v1/triggers/slack`. Engineers trigger investigations from any channel with plain-language descriptions. The report posts back to the thread.

**Human approval for high-severity incidents.** When severity exceeds the threshold, Reef posts a structured approval message to Slack with the full evidence and proposed action. One click is all it takes — no engineer needs to cross-reference five tools to decide.

**Multi-tenant deployments.** Each organization stores its own encrypted credentials in `organization_integrations`, isolated by org ID. Set `CORAL_ORGS_BASE_DIR` to a volume path for per-org Coral config directories. Teams share one Reef deployment; their tokens and data stay separated.

---

## Running Tests

```bash
cd backend
pytest -v
```

25 tests covering health, query executor, severity gate, orchestrator loop, and trigger endpoints.

---

## Repository Layout

```
coral_hackers/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # Triggers, investigations, webhooks, auth
│   │   ├── clients/        # Coral, GitHub, Vercel, Sentry, Slack, LLM
│   │   ├── services/       # Orchestrator, planner, judge, executor, evidence, severity, report
│   │   ├── db/             # SQLAlchemy models
│   │   └── schemas/        # Pydantic request/response models
│   ├── scripts/            # Coral source setup and trigger simulation
│   ├── tests/
│   └── docker-compose.yml
├── frontend/
│   └── src/
│       ├── api/            # Typed HTTP wrappers
│       ├── components/     # Shared UI
│       ├── contexts/       # Auth, Investigation, Theme
│       └── pages/          # Dashboard, Report, Auth
├── docs/
│   ├── architecture_diagram.txt
│   ├── implementation_status.md
│   └── reef_postman_collection.json
└── deploy/gce/             # Production deployment guide
```

---

## Built With

- [Coral](https://withcoral.ai) — SQL over APIs, cross-source JOINs, local execution
- [FastAPI](https://fastapi.tiangolo.com) — async Python web framework
- [React 19](https://react.dev) + TypeScript + Vite + Tailwind CSS — frontend
- [Gemini 2.5 Flash](https://aistudio.google.com) — planner LLM (free tier)
- [Groq / Llama 3.3 70B](https://console.groq.com) — judge LLM (free tier)
- [PostgreSQL](https://www.postgresql.org) — production database
- [Vercel](https://vercel.com) — frontend deployment

---

## Hackathon

Built for [Pirates of the Coral-bean](https://www.wemakedevs.org/hackathons/coral) — WeMakeDevs Coral Hackathon, Track 1: Enterprise Agent. May 25–31, 2026.
