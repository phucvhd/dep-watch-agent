"""Score saved runs' faithfulness with the RAGAS library and save it into each run, beside the
in-house judge's (``judge.py``), with how far the two agree.

    uv run --with ragas==0.4.4 python scripts/eval/ragas_judge.py <run.json>... [--limit N]

RAGAS runs in an overlay environment, not as a project dependency (see
``dep_watch_agent.eval.ragas_judge``). The judge is ``DEP_WATCH_RAGAS_MODEL`` at
``DEP_WATCH_RAGAS_BASE_URL`` with ``DEP_WATCH_RAGAS_API_KEY`` (any OpenAI-compatible API), and
may never be the model under test. ``--limit N`` scores only the first N issues, without saving:
a check that the judge answers in RAGAS's format before a whole run is spent on it.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from dep_watch_agent.eval import faithfulness as fa
from dep_watch_agent.eval import ragas_judge as rj
from dep_watch_agent.eval.dataset import load_dataset
from dep_watch_agent.eval.metrics import CaseResult

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", type=Path, nargs="+", help="eval/runs/<dataset>/<run>.json")
    parser.add_argument("--datasets", type=Path, default=ROOT / "eval/datasets")
    parser.add_argument("--limit", type=int, help="only the first N issues; nothing is saved")
    parser.add_argument("--force", action="store_true", help="score runs this judge already did")
    parser.add_argument(
        "--max-context-chars", type=int, default=fa.MAX_CONTEXT_CHARS,
        help="cut an issue's text read whole to this many characters (for token-per-minute caps)",
    )  # fmt: skip
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

    llm, judge_model = rj.judge_from_env()
    for path in args.runs:
        run = json.loads(path.read_text())
        fa.check_judge(judge_model, run.get("model") or run["system"])
        done = run.get("faithfulness_ragas") or {}
        if not args.force and args.limit is None and done.get("judge") == judge_model:
            print(f"{path.name}: already scored by {judge_model}, skipped", flush=True)
            continue
        data = load_dataset(args.datasets / run["dataset"])
        results = [CaseResult(**r) for r in run["results"]]
        if args.limit is not None:
            keys = list(dict.fromkeys(s.issue_key for s in rj.samples(results, data.issues)))
            results = [r for r in results if r.issue_key in keys[: args.limit]]
        scored = rj.score(results, data.issues, llm, max_context_chars=args.max_context_chars)
        judged = (run.get("faithfulness") or {}).get("judgments") or []
        out = {
            "judge": judge_model,
            **scored,
            "max_context_chars": args.max_context_chars,
            "agreement_with_inhouse": rj.agreement(scored["by_issue"], judged),
        }
        shown = {k: v for k, v in out.items() if k != "by_issue"}
        if args.limit is not None:
            print(f"{path.name} (first {args.limit} issues, not saved): {shown}", flush=True)
            continue
        run["faithfulness_ragas"] = out
        path.write_text(json.dumps(run, indent=2) + "\n")
        print(f"{path.name}: {shown}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
