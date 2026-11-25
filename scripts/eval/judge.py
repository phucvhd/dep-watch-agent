"""Score saved runs' faithfulness with the judge model, as
``POST /eval/runs/{dataset}/{run}/faithfulness`` does, and save it into each run.

    uv run python scripts/eval/judge.py <run.json>...

The judge is ``DEP_WATCH_JUDGE_MODEL`` (at ``DEP_WATCH_JUDGE_BASE_URL``, default the LLM's), and
may never be the model under test. Context recall over the labeled quotes needs no judge.
"""

import argparse
import json
import sys
from pathlib import Path

from dep_watch_agent.eval import faithfulness as fa
from dep_watch_agent.eval.dataset import load_dataset
from dep_watch_agent.eval.metrics import CaseResult
from dep_watch_agent.llm.extractor import load_prompt

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", type=Path, nargs="+", help="eval/runs/<dataset>/<run>.json")
    parser.add_argument("--datasets", type=Path, default=ROOT / "eval/datasets")
    parser.add_argument("--force", action="store_true", help="judge runs this judge already did")
    args = parser.parse_args(argv)

    judge, judge_model = fa.judge_from_env()
    prompt = load_prompt("judge_faithfulness").text
    for path in args.runs:
        run = json.loads(path.read_text())
        fa.check_judge(judge_model, run.get("model") or run["system"])
        if not args.force and (run.get("faithfulness") or {}).get("judge") == judge_model:
            print(f"{path.name}: already judged by {judge_model}, skipped", flush=True)
            continue
        data = load_dataset(args.datasets / run["dataset"])
        results = [CaseResult(**r) for r in run["results"]]
        run["faithfulness"] = {
            "judge": judge_model,
            **fa.score(results, data.issues, judge, prompt),
            "context_recall": fa.context_recall(results, fa.read_label_evidence(data.directory)),
        }
        path.write_text(json.dumps(run, indent=2) + "\n")
        shown = {k: v for k, v in run["faithfulness"].items() if k != "judgments"}
        print(path.name, shown, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
