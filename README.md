# Production Incident Intelligence Agent

**Pirates of the Coral-bean** — [WeMakeDevs Coral Hackathon](https://www.wemakedevs.org/hackathons/coral)  
**Dates:** May 25 – May 31 · **Track:** [Track 1 — Enterprise Agent](https://www.wemakedevs.org/hackathons/coral)

When something breaks, engineers often spend hours jumping between GitHub, Slack, monitoring, commits, ownership, and deployments. This agent compresses that into **one query**, **one investigation workflow**, and **one report** — then optionally helps remediate based on severity.

## Hackathon fit

This project targets **Track 1: Build an Enterprise Agent** — a real org problem solved with Coral-powered cross-source retrieval.

Closest official example voyage: **AI SRE Investigator** (PagerDuty + Datadog + GitHub + StatusGator). Our crew focuses on the same pain — correlating incidents with deploys, errors, and team context — using sources we can wire for the demo:

| Our sources | Role |
|-------------|------|
| GitHub | PRs, commits, ownership |
| Vercel | Deployments |
| Sentry | Errors / incidents |
| Slack | Incident threads, slash commands, human approval |

Coral’s pitch matches our core loop: one SQL query across multiple tools, no ETL, no glue code, data resolved inside Coral (not stuffed into the agent context). See the [hackathon page](https://www.wemakedevs.org/hackathons/coral) for rules, prizes, and judging criteria.

**Example query shape** (from the hackathon — same idea we automate):

```sql
-- Find root cause across tools in one query
SELECT g.title, s.error_message, sl.text
FROM github.pull_requests g
JOIN sentry.issues s
  ON s.first_seen >= g.merged_at
JOIN slack.messages sl
  ON sl.channel = '#incidents'
WHERE s.level = 'fatal'
ORDER BY s.first_seen DESC;
```

## Problem

Typical incident response today:

1. Check GitHub (PRs, commits, deploys)
2. Read Slack threads
3. Check monitoring / Sentry
4. Search for the owner
5. Correlate timelines manually

## Solution

An investigation system that automatically correlates:

- Deployments
- PRs
- Incidents
- Logs
- Slack discussions
- Ownership

into a single reasoning workflow powered by **[Coral](https://www.wemakedevs.org/hackathons/coral)** (SQL over APIs, cross-source JOINs, local execution).

After root cause is identified, a **severity gate** decides remediation:

| Severity | Mode | Behavior |
|----------|------|----------|
| ≤ 0.7 | Autonomous | Agent can proceed with fix workflow |
| > 0.7 | Human–agent paired | Agent asks permission before risky actions; human can take over |

## Judging alignment

How we map to [official criteria](https://www.wemakedevs.org/hackathons/coral):

| Criterion | How we address it |
|-----------|-------------------|
| Potential impact | Cuts multi-tool incident triage from hours to one workflow + report |
| Creativity & originality | Severity-gated remediation (autonomous vs human-paired) |
| Technical implementation | Orchestrated loop + Coral SQL executor + evidence store |
| Best use of Coral | Cross-source JOINs (GitHub + Sentry + Slack + deploys) in investigation queries |
| Aesthetics & UX | Dashboard API, Slack triggers, structured investigation reports |

## Repository layout

```text
coral_hackers/
├── README.md                          # This file
├── backend/                           # FastAPI incident agent service
│   ├── app/                           # API, services, clients, schemas
│   ├── tests/
│   └── README.md                      # Backend quick start
└── docs/
    ├── architecture_diagram.txt       # System architecture (ASCII)
    ├── backend_project_structure.md   # Backend folder map for the team
    └── hackathon.md                   # Hackathon links and track notes
```

## Architecture

See [`docs/architecture_diagram.txt`](docs/architecture_diagram.txt) for the full flow:

**External systems** → **Coral** → **Incident Agent Service** (triggers → orchestrator → planner/judge → query executor → evidence store → escalation → severity gate → report).

Backend implementation: [`docs/backend_project_structure.md`](docs/backend_project_structure.md).

## Coral setup (local)

From the [hackathon resources](https://www.wemakedevs.org/hackathons/coral):

```bash
brew install withcoral/tap/coral
coral source add <your-source>
# Query via CLI or MCP — credentials stay on your machine
```

Our backend calls Coral through `app/clients/coral_runtime_client.py` and `app/services/query_executor.py` (integration in progress).

## Quick start (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health`

Trigger an investigation (example):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/triggers/dashboard \
  -H "Content-Type: application/json" \
  -d '{"source": "dashboard", "query": "Why did checkout fail after the last deploy?"}'
```

More endpoints: [`backend/README.md`](backend/README.md).

## Team docs

| Document | Description |
|----------|-------------|
| [`docs/hackathon.md`](docs/hackathon.md) | Official links, track, dates, bounties |
| [`docs/architecture_diagram.txt`](docs/architecture_diagram.txt) | End-to-end system design |
| [`docs/backend_project_structure.md`](docs/backend_project_structure.md) | Backend folders and architecture mapping |
| [`docs/implementation_status.md`](docs/implementation_status.md) | **What has been built, layer by layer — start here** |
| [`docs/reef_postman_collection.json`](docs/reef_postman_collection.json) | Postman collection (17 requests, full lifecycle) |
| [`backend/README.md`](backend/README.md) | Run and test the API locally |

## Status

Backend fully implemented (Phases 1–3): real Coral CLI/mock integration, SQLite persistence, stateful orchestration loop, severity-gated remediation, 25 passing tests, and a Postman collection.

Next: wire frontend to real API, LLM planner (Phase 4B), Slack approval flow (Phase 6).

## Links

- [Hackathon — Pirates of the Coral-bean](https://www.wemakedevs.org/hackathons/coral)
- [WeMakeDevs](https://wemakedevs.org/)
- Coral docs / Discord / GitHub — linked from the hackathon sponsor section
