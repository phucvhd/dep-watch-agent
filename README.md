# dep-watch-agent

An agent that watches project dependencies for new releases, security advisories, and breaking changes.

## Status

Early scaffold — nothing implemented yet.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync                      # create .venv and install deps
uv run dep-watch-agent       # run the CLI
uv run pytest                # run tests
uv run ruff check .          # lint
uv run ruff format .         # format
```
