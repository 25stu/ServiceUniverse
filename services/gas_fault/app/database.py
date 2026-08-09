from __future__ import annotations

import os
import tempfile
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from services.gas_fault.app.models import Base

DEFAULT_DATA_DIRECTORY = Path(tempfile.gettempdir()) / "serviceuniverse"


def default_database_url() -> str:
    DEFAULT_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    database_path = DEFAULT_DATA_DIRECTORY / "gas_fault.sqlite3"
    return os.getenv(
        "GAS_DATABASE_URL",
        f"sqlite:///{database_path.as_posix()}",
    )


def create_database(
    database_url: str | None = None,
) -> tuple[Engine, sessionmaker[Session]]:
    url = database_url or default_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine_options: dict[str, object] = {"connect_args": connect_args}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        engine_options["poolclass"] = StaticPool
    engine = create_engine(url, **engine_options)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
