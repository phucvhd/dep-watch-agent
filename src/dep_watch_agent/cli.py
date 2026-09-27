import argparse

from dep_watch_agent import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dep-watch-agent",
        description="Watch project dependencies for releases, advisories, and breaking changes.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print("dep-watch-agent: nothing to do yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
