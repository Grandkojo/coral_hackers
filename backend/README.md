# Coral Incident Intelligence Agent (Backend)

FastAPI service implementing the architecture in `docs/architecture_diagram.txt`.

## Quick start

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -e .[dev]`
3. Copy environment template:
   - `cp .env.example .env`
4. Run the API:
   - `uvicorn app.main:app --reload`

## Initial endpoints

- `GET /health` - basic health check
- `POST /api/v1/triggers/dashboard` - dashboard-triggered investigation
- `POST /api/v1/triggers/slack` - Slack slash-command trigger
- `POST /api/v1/triggers/webhook` - generic webhook trigger
