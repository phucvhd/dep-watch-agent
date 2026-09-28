"""Postgres connection and schema migrations.

Application code talks to Postgres through psycopg directly. Schema changes are Alembic
revisions in ``dep_watch_agent/migrations/versions``, written as raw SQL. Create one with
``uv run alembic revision -m "..."``.
"""

import os

import psycopg
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, pool

DEFAULT_DATABASE_URL = "postgresql://dep_watch:dep_watch@localhost:5433/dep_watch"

# Arbitrary constant identifying the migration lock among this app's advisory locks.
MIGRATION_LOCK_ID = 7_361_204_518


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def sqlalchemy_url(url: str) -> str:
    """Point a plain ``postgresql://`` URL at SQLAlchemy's psycopg 3 driver."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def connect(url: str | None = None) -> psycopg.Connection:
    """Open an autocommit connection. Group writes with ``conn.transaction()``."""
    return psycopg.connect(url or database_url(), autocommit=True)


def alembic_config(url: str | None = None, *, schema: str | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", "dep_watch_agent:migrations")
    config.attributes["url"] = url or database_url()
    config.attributes["schema"] = schema
    return config


def migrate(url: str | None = None, *, schema: str | None = None, revision: str = "head") -> None:
    """Upgrade the database (or one schema in it) to ``revision``."""
    command.upgrade(alembic_config(url, schema=schema), revision)


def current_revision(url: str | None = None, *, schema: str | None = None) -> str | None:
    connect_args = {"options": f"-csearch_path={schema}"} if schema else {}
    engine = create_engine(
        sqlalchemy_url(url or database_url()), poolclass=pool.NullPool, connect_args=connect_args
    )
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()
