"""Alembic environment.

Migrations are hand-written SQL run through ``op.execute``; there are no ORM models, so
autogenerate is not used. The database URL comes from ``dep_watch_agent.db``, and callers can
target a specific schema (tests use throwaway schemas) via ``config.attributes["schema"]``.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

from dep_watch_agent.db import MIGRATION_LOCK_ID, database_url, sqlalchemy_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (``alembic upgrade head --sql``)."""
    context.configure(
        url=sqlalchemy_url(config.attributes.get("url") or database_url()),
        target_metadata=None,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = config.attributes.get("url") or database_url()
    schema = config.attributes.get("schema")
    connect_args = {"options": f"-csearch_path={schema}"} if schema else {}
    engine = create_engine(sqlalchemy_url(url), poolclass=pool.NullPool, connect_args=connect_args)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            # Serialize concurrent upgrades. Taken before Alembic reads the current revision,
            # so a process that waited sees the other's work and has nothing left to do.
            # Released automatically when the transaction ends.
            connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
