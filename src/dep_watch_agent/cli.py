import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from dep_watch_agent import __version__

DATASETS_DIR = Path("eval/datasets")
DEFAULT_DATASET = "kafka-ground-truth-v1"
DEFAULT_SEED = 20260927


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

    eval_cmd = commands.add_parser("eval", help="build and publish the ground-truth dataset")
    eval_commands = eval_cmd.add_subparsers(dest="eval_command", required=True)
    for sub, help_text in (
        ("sample", "sample issues and write a new dataset with an empty labels.csv"),
        ("status", "show labeling progress and problems"),
        ("upload", "upload a fully labeled dataset to Langfuse"),
    ):
        p = eval_commands.add_parser(sub, help=help_text)
        p.add_argument("--name", default=DEFAULT_DATASET, help=f"default: {DEFAULT_DATASET}")
        p.add_argument("--dir", type=Path, default=DATASETS_DIR, help=f"default: {DATASETS_DIR}")
        if sub == "sample":
            p.add_argument("--size", type=int, default=100, help="issues to sample (default: 100)")
            p.add_argument("--seed", type=int, default=DEFAULT_SEED)
            p.add_argument("--force", action="store_true", help="overwrite an existing dataset")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()  # .env in the working directory; real environment variables win
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "migrate":
        return _migrate()
    if args.command == "sync-jira":
        return _sync_jira(args.project, full=args.full, request_delay=args.request_delay)
    if args.command == "eval":
        return _eval(args)

    parser.print_help()
    return 0


def _migrate() -> int:
    from dep_watch_agent.db import current_revision, migrate

    before = current_revision()
    migrate()
    after = current_revision()
    if before == after:
        print(f"database already at revision {after}")
    else:
        print(f"migrated database from revision {before or '(empty)'} to {after}")
    return 0


def _sync_jira(project: str, *, full: bool, request_delay: float) -> int:
    from dep_watch_agent.db import migrate, session_factory
    from dep_watch_agent.jira.client import JiraClient
    from dep_watch_agent.jira.sync import sync_project

    def progress(count: int) -> None:
        if count % 500 == 0:
            print(f"  {count} issues synced", file=sys.stderr)

    migrate()
    with session_factory()() as session, JiraClient(request_delay=request_delay) as client:
        result = sync_project(session, client, project, full=full, on_issue=progress)

    since = result.since.isoformat() if result.since else "the beginning"
    print(
        f"{result.source}: synced {result.versions_synced} version(s) and "
        f"{result.issues_synced} issue(s) updated since {since}"
    )
    return 0


def _eval(args: argparse.Namespace) -> int:
    from dep_watch_agent.eval import dataset as ds

    directory = args.dir / args.name
    try:
        if args.eval_command == "sample":
            from dep_watch_agent.db import session_factory

            with session_factory()() as session:
                manifest, sample, cases = ds.sample_dataset(
                    session, args.name, size=args.size, seed=args.seed
                )
            ds.write_dataset(directory, manifest, sample, cases, force=args.force)
            print(f"wrote {len(sample)} issues and {len(cases)} cases to {directory}")
            print(f"strata: {manifest['strata_counts']}")
            print(f"case basis: {manifest['case_basis_counts']}")
            print(f"next: label {directory / 'labels.csv'} while reading {directory / 'review.md'}")
            return 0

        dataset = ds.load_dataset(directory)
        if args.eval_command == "status":
            labeled, total = ds.label_progress(dataset)
            problems = ds.label_problems(dataset)
            print(f"{dataset.name}: {labeled}/{total} cases labeled")
            for problem in [p for p in problems if not p.endswith("not labeled")]:
                print(f"  {problem}")
            if not problems:
                print("ready to upload")
            return 0 if not problems else 1

        from langfuse import Langfuse

        client = Langfuse()
        count = ds.upload(dataset, client)
        client.flush()
        print(f"uploaded {count} items to Langfuse dataset {dataset.name}")
        return 0
    except ds.DatasetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
