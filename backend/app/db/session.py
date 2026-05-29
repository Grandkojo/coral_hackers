from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base

_connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine = create_engine(settings.database_url, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _ensure_sqlite_columns() -> None:
    if "sqlite" not in settings.database_url:
        return
    inspector = inspect(engine)
    if not inspector.has_table("investigations"):
        return
    columns = {column["name"] for column in inspector.get_columns("investigations")}
    with engine.begin() as conn:
        if "approved_at" not in columns:
            conn.execute(text("ALTER TABLE investigations ADD COLUMN approved_at DATETIME"))
        if "organization_id" not in columns:
            conn.execute(
                text("ALTER TABLE investigations ADD COLUMN organization_id VARCHAR")
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
