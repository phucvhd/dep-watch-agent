# dep-watch-agent

Watches upstream issue trackers (starting with Apache Kafka's JIRA) for bugs that affect a
pinned dependency version: data loss, upgrade regressions, deadlocks and other issues that
never get a CVE.

## Status

- Version parsing and affected-range checks (`dep_watch_agent.versions`)
- Incremental JIRA sync into Postgres (`dep-watch-agent sync-jira`)

## Development

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
uv sync                          # create .venv and install deps
docker compose up -d --wait      # start Postgres (pgvector) on localhost:5433
uv run dep-watch-agent migrate   # apply database migrations
uv run dep-watch-agent sync-jira # sync KAFKA issues (incremental after the first run)
uv run pytest                    # run tests (DB tests skip if Postgres is down)
uv run ruff check .              # lint
uv run ruff format .             # format
```

Set `DATABASE_URL` to use a different Postgres (see `.env.example`). Tests use
`TEST_DATABASE_URL` if set, and each test runs in its own throwaway schema.

### Schema migrations

Migrations are [Alembic](https://alembic.sqlalchemy.org/) revisions in
`src/dep_watch_agent/migrations/versions/`, written as raw SQL with `op.execute`. There are no
ORM models, so autogenerate is not used.

```bash
uv run alembic revision -m "add foo table"   # new revision; fill in upgrade() and downgrade()
uv run alembic upgrade head                  # same as `dep-watch-agent migrate`
uv run alembic downgrade -1                  # undo the latest revision
uv run alembic history                       # list revisions
```

Every revision must have a working `downgrade()`; the test suite upgrades and downgrades each
one. If two branches both add a revision, merge the heads (`uv run alembic merge heads`)
before landing; a test fails when there is more than one head.

### JIRA sync

`sync-jira` pulls issues with their affected versions, fix versions, components and comments
from `issues.apache.org` anonymously. The first run fetches all ~20k KAFKA issues (about
7 minutes with the default 1 s delay between requests); later runs fetch only issues updated
since the previous run. Use `--full` to re-sync everything.
