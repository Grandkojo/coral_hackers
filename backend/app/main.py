from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.triggers import router as triggers_router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production Incident Intelligence Agent API",
)

app.include_router(health_router)
app.include_router(triggers_router, prefix="/api/v1")
