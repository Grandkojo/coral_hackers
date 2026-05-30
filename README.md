# Reef — Production Incident Intelligence Agent

**Reef compresses hours of cross-tool incident triage into a single investigation workflow.** It correlates signals across GitHub, Sentry, Vercel, and Slack, identifies a root cause, and either remediates autonomously or brings a human into the loop, based on severity.

---

## The Problem

When something breaks in production, engineers spend hours manually stitching together:

- Which PR landed just before the incident?
- Which errors surfaced in Sentry around the same time?
- What did the on-call thread in Slack say?
- Who owns the affected service?
- Did a Vercel deployment go out in that window?

The information is scattered across multiple tools, so engineers have to piece together the timeline manually. By the time the root cause is identified, the incident has often already caused significant impact.

**Reef automates the entire investigation.**

---

## How Reef Works

Reef runs a stateful investigation loop powered by [Coral](https://withcoral.ai). An SQL runtime that JOINs across GitHub, Sentry, Slack, and Vercel in a single query, with no ETL and no data leaving your machine.

Here is what a full investigation looks like:

**1. Trigger**: An incident arrives via the Reef dashboard, a Sentry webhook, or a `/reef` Slack slash command in your incident channel.

**2. Plan**: The Gemini planner LLM receives the full investigation context and decides which Coral SQL query to run next. It generates both the SQL and a rationale for why that query is the right next question.

**3. Execute**: Reef passes the query to Coral, which resolves data locally from your connected sources. Data never gets stuffed into the agent context.

**4. Judge**: The Groq judge LLM evaluates the returned evidence, scores confidence from 0.0 to 1.0, and extracts structured hypotheses about root cause.

**5. Repeat**: If confidence is below the threshold (default: 0.6), the planner generates the next query. The loop runs for up to 5 iterations.

**6. Escalate**: The escalation engine flags unresolved gaps: missing CODEOWNERS match, conflicting hypotheses, or insufficient evidence rows.

**7. Gate**: The severity gate applies a weighted score and decides: autonomous fix, or human approval required.

**8. Report**: Reef produces a structured report with a full timeline, suspected PRs, Coral query citations, and unresolved gaps.

Here is an example of a Coral query Reef generates during an investigation:

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

Reef connects to four platforms. Each one plays a different role across investigation and remediation.

### GitHub

**In investigation:** Reef queries `github.pull_requests` and `github.commits` to find changes that landed before the incident window. It uses `github.collaborators` or `github.teams` (based on your account type) to resolve service ownership via CODEOWNERS.

**In remediation:** Reef can open a revert PR against the suspected commit when operating in autonomous mode.

### Sentry

**In investigation:** Reef reads Sentry issues correlated by timestamp with recent deploys and PRs. Fatal error level adds a penalty to the severity score. Stack traces are included in query results for deeper signal.

**As a trigger:** Configure a Sentry Internal Integration to POST to Reef's webhook endpoint. Every new Sentry issue automatically kicks off an investigation.

### Vercel

**In investigation:** Reef queries Vercel deployment history to find what shipped before the incident. Deployment timestamps are used to anchor the correlation window across other sources.

**In remediation:** Reef can trigger a rollback on the identified deployment via the Vercel API when severity is low enough for autonomous action.

### Slack

**In investigation:** Reef reads incident channel message history to enrich context, oncall discussions, manually noted observations, and timestamps from the thread all feed into the investigation.

**As a trigger:** Engineers can start an investigation from any Slack channel with `/reef <natural language query>`. The report is posted back to the thread.

**As the human gate:** When severity is high, Reef posts a structured approval request to Slack. A human reviews the evidence and the proposed remediation action, then approves or rejects it with one click. Nothing is executed without that approval.

---

## AI Models

Reef uses two LLMs with distinct, non-overlapping roles in the investigation loop.

### Planner — Gemini 2.5 Flash

The planner answers: *what should we investigate next?*

At each iteration it receives the original query, all previous query results, and the hypotheses built so far. It outputs the next Coral SQL query and a plain-English rationale. The planner is optimized for structured reasoning about which JOIN and which timestamp window will most efficiently narrow the root cause.

Default provider: `gemini` · Default model: `gemini-2.5-flash`
Free tier via [Google AI Studio](https://aistudio.google.com/apikey) — no billing required.

### Judge — Groq (Llama 3.3 70B)

The judge answers: *is this evidence sufficient to stop?*

After each query execution, the judge scores the returned rows against the investigation context and outputs a confidence score (0.0–1.0) and a list of structured hypotheses. When confidence reaches 0.6 and a strong hypothesis is present, the loop terminates. The judge is optimized for speed — Groq's inference latency keeps the loop tight.

Default provider: `groq` · Default model: `llama-3.3-70b-versatile`
Free tier via [Groq Console](https://console.groq.com/keys) — no billing required.

### Supported Providers

Both roles accept `gemini`, `groq`, `openai`, or `anthropic`. Swap providers by setting `PLANNER_LLM_PROVIDER` and `JUDGE_LLM_PROVIDER` in your `.env`.

### Rules-Based Fallback

If no LLM keys are configured, Reef falls back automatically: a template-based planner runs a fixed query sequence, and a rules-based judge scores evidence using row count, fatal signal detection, and deployment correlation. The full investigation loop still runs — no LLM required.

---

## Severity Gate and Remediation

After root cause is identified, Reef scores the incident using a weighted formula:

- Base confidence score from the judge
- Blast radius (affected user count from Sentry)
- Fatal error penalty (`+0.15` when Sentry reports `fatal` level)
- Ownership gap penalty (`+0.05` when no CODEOWNERS match is found)

The score drives two distinct remediation modes:

| Severity Score | Mode | What Reef does |
|----------------|------|----------------|
| ≤ 0.7 | `autonomous_fix` | Reef proceeds: reverts the PR, rolls back the Vercel deployment, posts a resolution summary to Slack |
| > 0.7 | `human_agent_paired` | Reef posts a structured approval request to Slack with the full evidence and proposed action. A human approves or rejects before anything is executed |

High-severity incidents always have a human in the loop. Low-risk incidents resolve without paging anyone.

---

## Architecture

### Backend

The backend is a **FastAPI** service (Python 3.11+) that orchestrates the full investigation loop and exposes REST endpoints for triggering investigations, polling status, retrieving reports, and approving remediation.

**Core services:**

| Service | What it does |
|---------|-------------|
| `InvestigationOrchestrator` | Stateful loop controller — sequences planner → executor → judge per iteration |
| `LLMPlannerService` | Sends investigation context to Gemini, returns next `QueryPlan` (SQL + rationale) |
| `PlannerService` | Template-based fallback planner — fixed query sequence, no LLM needed |
| `QueryExecutor` | Validates SQL is read-only, runs it through Coral CLI or mock, normalizes rows |
| `EvidenceStore` | Persists each `QueryRun` to the database, returns `coral://query-run/{id}` citations |
| `LLMJudgeService` | Sends evidence rows to Groq/Gemini, returns confidence score and hypotheses |
| `JudgeService` | Rules-based fallback judge |
| `EscalationEngine` | Flags ownership gaps, conflicting hypotheses, and low-evidence loops |
| `SeverityGate` | Computes weighted severity score and sets `remediation_mode` |
| `ReportGenerator` | Builds `ReportResponse` (JSON) and a Markdown narrative |
| `SlackClient` | Posts investigation summaries, sends human approval requests |
| `CoralRuntimeClient` | Runs `coral sql` subprocess (or returns canned mock data in demo mode) |

**Database** (SQLAlchemy ORM — SQLite in development, PostgreSQL in production):

| Table | Contents |
|-------|---------|
| `investigations` | Status, confidence score, severity score, remediation mode, timestamps |
| `query_runs` | SQL executed, rows returned, iteration number, per-investigation |
| `report_snapshots` | Finalized JSON payload and rendered Markdown |
| `organizations` | Multi-tenant org records |
| `users` | User accounts scoped to an organization |
| `organization_integrations` | Encrypted per-org credentials (GitHub, Sentry, Slack, Vercel) |

**Coral** runs in two modes controlled by `CORAL_MODE`:
- `mock` — returns canned "checkout failed" demo data. No Coral install needed. Good for development.
- `cli` — runs real `coral sql` subprocesses against your connected sources. Requires Coral CLI installed and sources configured.

### Frontend

The frontend is a **React 19 + TypeScript** app built with Vite, styled with Tailwind CSS, and deployed on Vercel. It communicates with the FastAPI backend via typed HTTP client wrappers.

**Pages:**

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Trigger form, active investigation panel, history list |
| Report | `/report/:reportId` | Full report view with timeline, suspects, and citations |
| Login / Signup | `/login`, `/signup` | JWT authentication (multi-tenant) |

**Key components:**

| Component | Description |
|-----------|-------------|
| `InvestigationForm` | Natural language query input and Vercel deployment URL paste |
| `InvestigationPanel` | Live investigation status with per-iteration timeline updates |
| `ReportPanel` | Root cause, suspects, Coral citations, unresolved gaps |
| `ReportTimeline` | Visual incident timeline rendered from report data |
| `SeverityBar` | Color-coded severity indicator from 0.0 to 1.0 |
| `SourceBadges` | Platform icons for GitHub, Sentry, Slack, and Vercel |

**Stack:** React 19.2.6 · TypeScript · Vite 8 · React Router v7 · Tailwind CSS 4.3 · Three.js (ambient backdrop) · Vercel (deployment)

**State:** `InvestigationContext` (active investigation), `AuthContext` (JWT session), `ThemeContext` (light/dark)

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

The fastest path. No external database, no Coral install required.

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

Backend runs at `http://127.0.0.1:8000` · Frontend at `http://localhost:5173`

Trigger a test investigation:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"query": "Why did checkout fail after the last deploy?"}'
```

Or paste a Vercel deployment URL:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"vercel_url": "dpl_EEWWZ361mMHt6cnfxB3cFWQkChnv"}'
```

To run all 8 dashboard scenarios and 4 Sentry webhooks at once:

```bash
./scripts/simulate_triggers.sh all
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

# Non-interactive setup using env vars
cp backend/.env.example backend/.env   # fill GITHUB_TOKEN, SENTRY_ORG, SENTRY_TOKEN, SLACK_TOKEN
set -a && source backend/.env && set +a
./scripts/setup_coral_sources.sh
```

Manual setup:

```bash
coral source add github   # reads GITHUB_TOKEN from env
coral source add sentry   # reads SENTRY_ORG, SENTRY_TOKEN
coral source add slack    # reads SLACK_TOKEN
coral source add vercel   # reads VERCEL_TOKEN

# Verify sources
coral sql "SELECT schema_name, table_name FROM coral.tables LIMIT 20"
```

### Production — GCE + nginx + Let's Encrypt

Full guide: [`deploy/gce/README.md`](deploy/gce/README.md)

- **VM:** GCE e2-medium, Ubuntu 24.04, 30 GB
- **Backend:** Docker Compose (Postgres 16 + FastAPI) on the VM
- **TLS:** nginx reverse proxy + Certbot auto-renewal
- **Frontend:** Vercel with `VITE_API_BASE_URL=https://api.yourdomain.com`

---

## Configuration

All configuration lives in `backend/.env`. Start from `backend/.env.example`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./reef.db` | SQLite for dev · Postgres connection string for production |
| `CORAL_MODE` | `mock` | `mock` for canned demo data · `cli` for real Coral queries |
| `CORAL_BINARY` | `coral` | Path to the Coral CLI binary |
| `CORAL_SQL_TIMEOUT` | `30` | Seconds before a Coral query times out |
| `MAX_INVESTIGATION_ITERATIONS` | `5` | Max orchestrator loop iterations per investigation |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimum confidence score to stop the loop |
| `SEVERITY_THRESHOLD` | `0.7` | Above this → `human_agent_paired` mode |

### Platform credentials

| Variable | Used for |
|----------|---------|
| `GITHUB_TOKEN` | Coral GitHub source + PR revert (remediation) |
| `GITHUB_OWNER` | Coral `github.pulls` and ownership filters |
| `GITHUB_REPO` | Coral `github.pulls` and ownership filters |
| `GITHUB_ACCOUNT_TYPE` | `user` → `github.collaborators` · `org` → `github.teams` |
| `SENTRY_ORG` | Coral Sentry source |
| `SENTRY_TOKEN` | Coral Sentry source |
| `SLACK_TOKEN` | Coral Slack reads (incident threads) |
| `SLACK_BOT_TOKEN` | Slack notifications and approval gate posts |
| `SLACK_SIGNING_SECRET` | Slash command request verification |
| `VERCEL_TOKEN` | Coral Vercel source + deployment rollback |
| `VERCEL_TEAM_ID` | Team-scoped Vercel queries |

### AI models

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANNER_LLM_PROVIDER` | `gemini` | `gemini`, `groq`, `openai`, or `anthropic` |
| `JUDGE_LLM_PROVIDER` | `groq` | `groq`, `gemini`, `openai`, or `anthropic` |
| `GEMINI_API_KEY` | _(empty)_ | Free at [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | _(empty)_ | Free at [console.groq.com](https://console.groq.com/keys) |
| `PLANNER_MODEL` | `gemini-2.5-flash` | Override planner model ID |
| `JUDGE_MODEL` | `llama-3.3-70b-versatile` | Override judge model ID |

### Auth and multi-tenancy

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Secret key for JWT signing |
| `CREDENTIALS_ENCRYPTION_KEY` | Fernet key for encrypting per-org integration tokens |
| `AUTH_REQUIRED` | `true` to enforce JWT on all endpoints |
| `CORAL_ORGS_BASE_DIR` | Base directory for per-org Coral config volumes |

---

## API Reference

### Trigger endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/triggers/dashboard` | Start an investigation from the UI |
| `POST` | `/api/v1/triggers/slack` | Start an investigation from a Slack slash command |
| `POST` | `/api/v1/webhooks/sentry` | Async investigation triggered by Sentry webhook |

**Response shape** (`ReportResponse`):

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

### Investigation endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/investigations/{id}` | Poll status and live confidence during the loop |
| `GET` | `/api/v1/investigations/{id}/report` | Retrieve the finalized report |
| `POST` | `/api/v1/investigations/{id}/approve` | Approve remediation for `human_agent_paired` mode |

**Poll response:**

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

### Health

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}
```

Swagger UI: `http://127.0.0.1:8000/docs`

A Postman collection with 17 pre-wired requests (trigger → poll → approve → verify) is at [`docs/reef_postman_collection.json`](docs/reef_postman_collection.json).

---

## Integrating with Your Team

Reef is designed to plug into your existing incident response workflow, not replace it.

### Connect Sentry alerts as investigation triggers

In **Sentry → Settings → Developer Settings → Internal Integrations**, create an integration and point the webhook URL at:

```
POST https://your-reef-host/api/v1/webhooks/sentry
```

Every new Sentry issue now automatically triggers a Reef investigation. Your on-call engineer receives a Slack message when the report is ready — without manually starting anything.

### Add `/reef` to your incident Slack channel

Configure the Slack slash command to point at:

```
POST https://your-reef-host/api/v1/triggers/slack
```

Engineers can trigger an investigation from any Slack channel with a plain-language description of the problem. The report posts back to the thread.

### Keep humans in the loop for high-severity incidents

When severity exceeds the threshold, Reef posts a structured approval request to a configured Slack channel. The message includes the full evidence, the suspected PR, and the proposed remediation action. One approval or rejection is all that's needed — no engineer has to read five tools to make the call.

### Swap in your own LLMs

Set `PLANNER_LLM_PROVIDER` and `JUDGE_LLM_PROVIDER` to `openai` or `anthropic` if your team already manages those credentials. The free Gemini + Groq defaults require no billing account to start.

### Multi-tenant deployments

Each organization is isolated with its own row in `organizations` and its own encrypted credentials in `organization_integrations`. Set `CORAL_ORGS_BASE_DIR` to a volume path and Reef will maintain a per-org Coral config directory. Teams share one Reef deployment; their data and tokens stay separated.

---

## Running Tests

```bash
cd backend
pytest -v
```

The test suite has 25 tests covering: health endpoints, query executor (mock rows, read-only SQL guard, row normalization), severity gate (threshold logic, fatal and ownership penalties), orchestrator (full loop, citation output, timeline), and trigger endpoints (end-to-end dashboard and Slack flows).

---

## Repository Layout

```
coral_hackers/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Triggers, investigations, webhooks, auth
│   │   ├── clients/             # Coral, GitHub, Vercel, Sentry, Slack, LLM clients
│   │   ├── core/                # Config, logging, security
│   │   ├── db/                  # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request and response models
│   │   └── services/            # Orchestrator, planner, judge, executor, evidence, severity, report
│   ├── scripts/                 # Coral source setup and trigger simulation
│   ├── tests/
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/                 # Typed HTTP wrappers (triggers, investigations)
│   │   ├── components/          # Shared UI components
│   │   ├── contexts/            # Auth, Investigation, Theme providers
│   │   ├── pages/               # Route-level pages
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # TypeScript interfaces
│   ├── vercel.json
│   └── README.md
├── docs/
│   ├── architecture_diagram.txt
│   ├── backend_project_structure.md
│   ├── implementation_status.md
│   └── reef_postman_collection.json
├── deploy/
│   └── gce/                     # GCE production deployment guide and scripts
└── data/                        # Per-org Coral config directories
```

---

## Built With

- [Coral](https://withcoral.ai) — SQL over APIs, cross-source JOINs, local execution
- [FastAPI](https://fastapi.tiangolo.com) — async Python web framework
- [React 19](https://react.dev) — frontend framework
- [Vite](https://vitejs.dev) — frontend build tool
- [Tailwind CSS](https://tailwindcss.com) — styling
- [Gemini 2.5 Flash](https://aistudio.google.com) — investigation planner LLM (free tier)
- [Groq / Llama 3.3 70B](https://console.groq.com) — evidence judge LLM (free tier)
- [PostgreSQL](https://www.postgresql.org) — production database
- [Vercel](https://vercel.com) — frontend deployment

---

## Hackathon

Built for [Pirates of the Coral-bean](https://www.wemakedevs.org/hackathons/coral) — WeMakeDevs Coral Hackathon, Track 1: Enterprise Agent. May 25–31, 2026.