"""Alembic environment.

``target_metadata`` is the SQLAlchemy models' metadata, so ``alembic revision --autogenerate``
and ``alembic check`` compare the models against the database. The database URL comes from
``dep_watch_agent.db``, and callers can target a specific schema (tests use throwaway schemas)
via ``config.attributes["schema"]``.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import text

from dep_watch_agent.db import MIGRATION_LOCK_ID, create_db_engine, database_url, sqlalchemy_url
from dep_watch_agent.orm import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (``alembic upgrade head --sql``)."""
    context.configure(
        url=sqlalchemy_url(config.attributes.get("url") or database_url()),
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_db_engine(config.attributes.get("url"), schema=config.attributes.get("schema"))

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
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
