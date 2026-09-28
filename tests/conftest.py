import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from dep_watch_agent.db import create_db_engine, database_url, migrate

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    def load(name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    return load


@dataclass(frozen=True)
class ThrowawaySchema:
    url: str
    name: str

    def engine(self) -> Engine:
        return create_db_engine(self.url, schema=self.name)

    def session(self) -> Session:
        return Session(self.engine())


@pytest.fixture
def schema():
    """An empty throwaway schema, dropped after the test.

    Uses TEST_DATABASE_URL, falling back to DATABASE_URL and then the docker-compose default.
    Skips if no Postgres is reachable; start one with ``docker compose up -d``.
    """
    url = os.environ.get("TEST_DATABASE_URL") or database_url()
    admin = create_db_engine(url)
    try:
        with admin.connect():
            pass
    except OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {url}: {str(exc.orig).splitlines()[0]}")

    name = f"test_{uuid.uuid4().hex[:12]}"
    with admin.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {name}"))
    try:
        yield ThrowawaySchema(url=url, name=name)
    finally:
        with admin.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {name} CASCADE"))
        admin.dispose()


@pytest.fixture
def db(schema):
    """Session on a throwaway schema migrated to head. Closed (rolled back) after the test."""
    migrate(schema.url, schema=schema.name)
    with schema.session() as session:
        yield session
