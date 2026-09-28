import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import psycopg
import pytest

from dep_watch_agent.db import connect, database_url, migrate

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

    def connect(self) -> psycopg.Connection:
        conn = connect(self.url)
        conn.execute(f"SET search_path TO {self.name}")
        return conn


@pytest.fixture
def schema():
    """An empty throwaway schema, dropped after the test.

    Uses TEST_DATABASE_URL, falling back to DATABASE_URL and then the docker-compose default.
    Skips if no Postgres is reachable; start one with ``docker compose up -d``.
    """
    url = os.environ.get("TEST_DATABASE_URL") or database_url()
    try:
        admin = connect(url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {url}: {str(exc).splitlines()[0]}")

    name = f"test_{uuid.uuid4().hex[:12]}"
    admin.execute(f"CREATE SCHEMA {name}")
    try:
        yield ThrowawaySchema(url=url, name=name)
    finally:
        admin.execute(f"DROP SCHEMA {name} CASCADE")
        admin.close()


@pytest.fixture
def db(schema):
    """Connection to a throwaway schema migrated to head."""
    migrate(schema.url, schema=schema.name)
    conn = schema.connect()
    try:
        yield conn
    finally:
        conn.close()
