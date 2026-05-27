# Backend Project Structure (FastAPI)

This document explains the initial backend scaffold for the **Production Incident Intelligence Agent** — our [Track 1 Enterprise Agent](https://www.wemakedevs.org/hackathons/coral) for **Pirates of the Coral-bean**.

It maps directly to `docs/architecture_diagram.txt`. Hackathon links and track notes: `docs/hackathon.md`.

## Folder Tree 

```text
backend/
├── .env.example
├── README.md
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       └── triggers.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── coral_runtime_client.py
│   │   ├── github_client.py
│   │   ├── vercel_client.py
│   │   ├── sentry_client.py
│   │   └── slack_client.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── trigger.py
│   │   ├── investigation.py
│   │   └── report.py
│   └── services/
│       ├── __init__.py
│       ├── investigation_orchestrator.py
│       ├── planner_service.py
│       ├── judge_service.py
│       ├── query_executor.py
│       ├── evidence_store.py
│       ├── escalation_engine.py
│       ├── severity_gate.py
│       └── report_generator.py
└── tests/
    ├── __init__.py
    └── test_health.py
```

## Architecture Mapping

- **Trigger Layer**  
  Implemented in `app/api/routes/triggers.py` with routes for dashboard, Slack, and webhooks.

- **Investigation Orchestrator**  
  Implemented in `app/services/investigation_orchestrator.py` as the stateful loop driver.

- **Planner LLM + Judge LLM**  
  Located in `app/services/planner_service.py` and `app/services/judge_service.py`.

- **Query Executor**  
  Located in `app/services/query_executor.py` (initial placeholder to connect Coral Runtime).

- **Evidence Store**  
  Located in `app/services/evidence_store.py` (placeholder to persist query/evidence snapshots).

- **Escalation Engine**  
  Located in `app/services/escalation_engine.py` for confidence and conflict checks.

- **Severity + Remediation Gate**  
  Located in `app/services/severity_gate.py`, with:
  - `severity <= 0.7` => `autonomous_fix`
  - `severity > 0.7` => `human_agent_paired`

- **Report Generator**  
  Located in `app/services/report_generator.py` for markdown/JSON-ready output payloads.

## Next Implementation Steps

1. Replace placeholders in `clients/` with authenticated API integrations.
2. Replace mock SQL execution with real Coral runtime query calls.
3. Persist investigation state/evidence in database tables via SQLAlchemy models.
4. Add Slack interaction flow for human approval in high-severity mode.
5. Add test coverage for orchestrator paths and severity gate decisions.
