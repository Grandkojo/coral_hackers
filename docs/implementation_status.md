# Reef — Implementation Status

**Project:** Pirates of the Coral-bean · [WeMakeDevs Coral Hackathon](https://www.wemakedevs.org/hackathons/coral)  
**Track:** Track 1 — Enterprise Agent  
**Stack:** Python 3.11+ · FastAPI · SQLAlchemy · Coral CLI/MCP  
**Last updated:** 2026-05-26

---

## What is Reef?

Reef is a **Production Incident Intelligence Agent**. When something breaks in production, engineers normally jump between GitHub, Sentry, Slack, and Vercel manually for hours to correlate the root cause. Reef compresses that into a single query — running a stateful investigation loop powered by [Coral](https://withcoral.com/docs) (SQL over APIs, cross-source JOINs, local execution) — and produces a structured report with a timeline, top suspects, citations, and a severity-gated remediation decision.

Architecture reference: [`docs/architecture_diagram.txt`](architecture_diagram.txt)

---

## What has been implemented

### Layer 1 — Config & infrastructure

| File | What it does |
|------|-------------|
| `app/core/config.py` | `CoralMode` enum (`cli` / `mock`), all settings including Coral binary path, iteration limits, confidence & severity thresholds, LLM placeholder for Phase 4B |
| `app/core/logging.py` | `configure_logging()` + `get_logger(name)` helper used across every service |
| `.env.example` | Full annotated env template — every variable documented with its effect |

---

### Layer 2 — Database (SQLAlchemy + SQLite)

Three models wired together to persist the full investigation lifecycle:

| Model | Table | Stores |
|-------|-------|--------|
| `Investigation` | `investigations` | ID, status, source, user query, iteration count, confidence score, root cause, severity score, remediation mode, timestamps |
| `QueryRun` | `query_runs` | One row per Coral query — SQL, rationale, row count, raw JSON rows, iteration number |
| `ReportSnapshot` | `report_snapshots` | Finalized `ReportResponse` as JSON + rendered markdown |

`init_db()` is called from the FastAPI lifespan so tables are created automatically on first boot. `get_db()` provides the standard SQLAlchemy session dependency.

---

### Layer 3 — Coral client + query executor

**`app/clients/coral_runtime_client.py`**

Two modes controlled by `CORAL_MODE`:

| Mode | Behaviour |
|------|-----------|
| `mock` (default) | Returns canned "checkout failed after last deploy" demo rows — realistic PR, Sentry, Slack, Vercel, and ownership data. Safe without Coral installed. |
| `cli` | Calls `coral sql --output json "<query>"` as a subprocess. Needs `brew install withcoral/tap/coral` and configured sources. |

The mock dataset tells a coherent story: PR #234 "refactor checkout payment validation" merges at 18:42, a fatal `TypeError: Cannot read properties of undefined (reading 'amount')` appears at 18:47, Slack erupts in `#incidents`, and a rollback is posted at 19:02.

**`app/services/query_executor.py`**

- Read-only SQL guard — rejects anything that doesn't start with `SELECT`, `WITH`, or `EXPLAIN`
- Row normalization — drops all-None entries
- Wraps `CoralQueryError` as `QueryExecutionError` with structured logging

---

### Layer 4 — Schemas

| Schema | Key additions vs scaffold |
|--------|--------------------------|
| `InvestigationState` | `status` enum, `QueryPlan` list, typed `Hypothesis` list (text + confidence + source_refs), `escalation_flags` dict |
| `TriggerRequest` | unchanged |
| `TriggerResponse` | new — `investigation_id`, `status`, `poll_url` (for future async path) |
| `ReportResponse` | added `root_cause` field |

---

### Layer 5 — Services (the core loop)

Every service maps to a box in `docs/architecture_diagram.txt`.

#### `PlannerService`
Template-based planner — five curated Coral queries run in order each investigation:

| Iteration | Query | Purpose |
|-----------|-------|---------|
| 0 | `coral.tables` | Discover available sources before querying |
| 1 | `github.pull_requests JOIN sentry.issues` | Correlate PRs merged before fatal errors |
| 2 | `slack.messages WHERE channel = '#incidents'` | Pull incident thread context |
| 3 | `vercel.deployments` | Deployment timeline |
| 4 | `github.codeowners` | Ownership lookup for remediation routing |

Swappable for an LLM planner in Phase 4B — same interface, `plan_next_query()` returns a `QueryPlan`.

#### `JudgeService`
Rules-based evidence scoring:
- **Confidence delta** per iteration: base row count score + +0.15 for fatal signals + +0.10 for deploy correlation signals
- **Hypothesis extraction**: PR↔error pairs → `confidence 0.65`; Slack context → `confidence 0.30`; ownership → `confidence 0.50`
- **Sufficiency check**: `confidence >= 0.6` + at least one row + at least one strong hypothesis with source refs

#### `EvidenceStore`
Replaces the previous no-op. Persists:
- `create()` — opens the investigation record on loop start
- `append_query_run()` — saves each Coral query + its rows, returns a `coral://query-run/{id}` citation URI
- `save()` — mid-loop update (confidence + iteration count)
- `finalize()` — writes completed status, severity, remediation mode, and the full report snapshot

#### `EscalationEngine`
Evaluates three flags after the loop exits:
- `sufficient_evidence` — confidence ≥ 0.6
- `conflicting_hypotheses` — many hypotheses but none strong
- `missing_ownership` — no hypothesis starting with `owner:`

These flags feed directly into `unresolved_gaps` in the report.

#### `SeverityGate`
Weighted score in `[0, 1]`:

| Component | Contribution |
|-----------|-------------|
| Confidence score | base |
| Blast radius | `min(0.20, affected_users / 1000)` |
| Fatal error present | +0.15 |
| Ownership gap | +0.05 |

`severity <= 0.7` → `autonomous_fix`  
`severity > 0.7` → `human_agent_paired` (triggers Slack approval request)

#### `InvestigationOrchestrator`
The stateful loop controller. Implements the architecture diagram exactly:

```
trigger → create investigation record
loop (max 5 iterations):
    planner  → QueryPlan (sql + rationale)
    executor → Coral rows
    judge    → update confidence + extract hypotheses
    store    → persist query run, get citation
    check    → stop if sufficient evidence
escalation engine → flags
severity gate     → score + mode
report generator  → ReportResponse + markdown
store.finalize()  → write report snapshot
```

#### `ReportGenerator`
Produces two outputs simultaneously:
- `ReportResponse` — structured JSON (used by the API and frontend)
- Markdown string — stored in `ReportSnapshot.markdown` for display

---

### Layer 6 — API routes

| Route | Method | Description |
|-------|--------|-------------|
| `/health` | GET | Liveness check |
| `/api/v1/triggers/dashboard` | POST | Start investigation from UI |
| `/api/v1/triggers/slack` | POST | Start from Slack slash command |
| `/api/v1/triggers/webhook` | POST | Start from webhook / PagerDuty |
| `/api/v1/investigations/{id}` | GET | Poll status + live confidence |
| `/api/v1/investigations/{id}/report` | GET | Retrieve finalized report |
| `/api/v1/investigations/{id}/approve` | POST | Human approval gate |

All trigger routes use FastAPI `Depends()` to inject a fresh `EvidenceStore(db)` → `InvestigationOrchestrator` per request — no shared mutable state between calls.

---

### Layer 7 — Clients

**`SlackClient`** — used on the remediation path only (not for investigation reads, which go through Coral):
- `post_message(channel_id, text)` — post to any channel
- `fetch_incident_threads(channel_id)` — read channel history
- `request_approval(channel_id, investigation_id, root_cause, severity_score)` — structured human-approval message with approve command

`github_client.py` and `vercel_client.py` remain stubs — investigation data for those sources flows through Coral, not direct API calls.

---

### Layer 8 — Tests

**25 tests, all passing.**

| File | Tests | Covers |
|------|-------|--------|
| `test_health.py` | 1 | Existing health endpoint |
| `test_query_executor.py` | 6 | Mock rows, read-only guard (INSERT/DROP rejected), normalization |
| `test_severity_gate.py` | 7 | Threshold boundary (0.70/0.71), fatal penalty, blast radius cap, ownership penalty, score clamped to 1 |
| `test_orchestrator.py` | 6 | Full loop with mock store: returns report, finds root cause, has citations, has timeline, evidence_store called |
| `test_triggers.py` | 5 | Dashboard trigger, Slack trigger, missing query → 422, end-to-end real DB loop |

---

### Layer 9 — Testing tooling

**`docs/reef_postman_collection.json`** — 17 Postman requests across 6 folders:

| Folder | Requests |
|--------|----------|
| 0 · Health | 1 |
| 1 · Trigger investigation | 3 (dashboard, Slack, webhook) |
| 2 · Poll investigation | 2 (status, report) |
| 3 · Remediation gate | 1 (conditional approve) |
| 4 · Edge cases | 5 (422s, 404s) |
| 5 · Full flow (automated) | 5 (complete lifecycle in one runner pass) |

The collection auto-saves `investigation_id` from the dashboard trigger and uses it for all polling and approval requests.

---

## What is NOT yet built

| Item | Phase | Notes |
|------|-------|-------|
| Real Coral source queries | Phase 1b | Set `CORAL_MODE=cli` and `coral source add github/sentry/slack` |
| LLM planner / judge | Phase 4B | `OPENAI_API_KEY` wired in config; `PlannerService` interface is ready to swap |
| Slack approval → autonomous fix | Phase 6 | `SlackClient.request_approval()` exists; `remediation_service.py` not yet written |
| GitHub/Vercel write actions | Phase 6 | Needed for "revert PR", "rollback deployment" autonomous actions |
| Async investigation + polling | Phase 5 | `TriggerResponse` schema exists; routes still synchronous |
| `GET /investigations` list | Phase 5 | Would complete the dashboard UI data contract |
| Alembic migrations | Phase 2b | `create_all` used for now; Alembic in `pyproject.toml` deps |
| Frontend ↔ backend wire-up | Phase 5 | Frontend still uses mock data in `App.tsx` |

---

## Running the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

| Check | Command |
|-------|---------|
| Health | `curl http://127.0.0.1:8000/health` |
| Run tests | `pytest -v` |
| API docs | `http://127.0.0.1:8000/docs` |

To switch from mock to real Coral:

```bash
# .env
CORAL_MODE=cli
CORAL_BINARY=coral  # full path if not in PATH
```

Then add your sources:

```bash
coral source add github
coral source add sentry
coral source add slack
```
