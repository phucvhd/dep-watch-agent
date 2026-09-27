import json
import os
import uuid
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


@pytest.fixture
def db():
    """Migrated connection in a throwaway schema, dropped after the test.

    Uses TEST_DATABASE_URL, falling back to DATABASE_URL and then the docker-compose default.
    Skips if no Postgres is reachable; start one with ``docker compose up -d``.
    """
    url = os.environ.get("TEST_DATABASE_URL") or database_url()
    try:
        conn = connect(url)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres not reachable at {url}: {str(exc).splitlines()[0]}")

    schema = f"test_{uuid.uuid4().hex[:12]}"
    conn.execute(f"CREATE SCHEMA {schema}")
    conn.execute(f"SET search_path TO {schema}")
    try:
        migrate(conn)
        yield conn
    finally:
        conn.execute(f"DROP SCHEMA {schema} CASCADE")
        conn.close()
