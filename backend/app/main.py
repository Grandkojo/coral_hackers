from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.investigations import router as investigations_router
from app.api.routes.triggers import router as triggers_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production Incident Intelligence Agent — Reef",
    lifespan=lifespan,
)

_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health_router)
app.include_router(triggers_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(investigations_router, prefix="/api/v1")
