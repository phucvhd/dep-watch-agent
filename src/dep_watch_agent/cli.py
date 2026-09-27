import argparse
import sys

from dep_watch_agent import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dep-watch-agent",
        description="Watch upstream issue trackers for bugs affecting a pinned dependency version.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("migrate", help="apply database migrations")

    sync = commands.add_parser("sync-jira", help="sync issues from Apache JIRA into Postgres")
    sync.add_argument("--project", default="KAFKA", help="JIRA project key (default: KAFKA)")
    sync.add_argument(
        "--full", action="store_true", help="ignore the watermark and re-sync every issue"
    )
    sync.add_argument(
        "--request-delay",
        type=float,
        default=1.0,
        help="seconds to wait between JIRA requests (default: 1.0)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "migrate":
        return _migrate()
    if args.command == "sync-jira":
        return _sync_jira(args.project, full=args.full, request_delay=args.request_delay)

    parser.print_help()
    return 0


def _migrate() -> int:
    from dep_watch_agent.db import connect, migrate

    with connect() as conn:
        applied = migrate(conn)
    print(f"applied {len(applied)} migration(s)" + (f": {', '.join(applied)}" if applied else ""))
    return 0


def _sync_jira(project: str, *, full: bool, request_delay: float) -> int:
    from dep_watch_agent.db import connect, migrate
    from dep_watch_agent.jira.client import JiraClient
    from dep_watch_agent.jira.sync import sync_project

    def progress(count: int) -> None:
        if count % 500 == 0:
            print(f"  {count} issues synced", file=sys.stderr)

    with connect() as conn, JiraClient(request_delay=request_delay) as client:
        migrate(conn)
        result = sync_project(conn, client, project, full=full, on_issue=progress)

    since = result.since.isoformat() if result.since else "the beginning"
    print(f"{result.source}: synced {result.issues_synced} issue(s) updated since {since}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
