#!/usr/bin/env bash
# The proposal's experiment matrix on LM Studio: every model's variants, one model loaded at a
# time (so a run's latency is its own model's and memory stays within 16 GB), then judged
# faithfulness for the Qwen3-4B runs (RQ3) and, with Langfuse keys, every new run replayed as
# a Langfuse experiment. Each run is saved to $DEP_WATCH_RUNS_DIR/<dataset>/<run>.json.
#
#   scripts/eval/run_matrix.sh                 # all models
#   scripts/eval/run_matrix.sh qwen/qwen3.5-9b # only the models named
#
# Needs Postgres (hybrid retrieval stores passages there) and the models downloaded in LM
# Studio. Reads .env. Overrides: LMS (the lms CLI), DATASET, JUDGE, DEP_WATCH_RUNS_DIR.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi

LMS=${LMS:-$HOME/.lmstudio/bin/lms}
DATASET=${DATASET:-kafka-ground-truth-v2}
JUDGE=${JUDGE:-qwen/qwen3.5-9b}
EMBED=${DEP_WATCH_EMBED_MODEL:-text-embedding-qwen3-embedding-0.6b}
export DEP_WATCH_RUNS_DIR=${DEP_WATCH_RUNS_DIR:-eval/runs}
RUNS=$DEP_WATCH_RUNS_DIR/$DATASET
CONTEXT=16384

# model | variants | max output tokens (reasoning models think first, so they get more)
MATRIX=(
  "qwen/qwen3-4b-2507|zeroshot,fewshot,cot,direct,hybrid|"
  "google/gemma-4-e4b|zeroshot,fewshot,direct|8192"
  "qwen/qwen3.5-9b|zeroshot,fewshot,direct|8192"
  "meta-llama-3.1-8b-instruct|zeroshot,fewshot,direct|"
)
# Judged runs (the judge is never the model under test).
JUDGED=(qwen3-4b-2507 qwen3-4b-2507-fewshot qwen3-4b-2507-hybrid)

wanted() {  # true if no model was named, or this one was
  [[ $# -eq 1 ]] && return 0
  local model=$1; shift
  for name in "$@"; do [[ $name == "$model" ]] && return 0; done
  return 1
}

started=$(mktemp)
trap 'rm -f "$started"; "$LMS" unload --all >/dev/null 2>&1 || true' EXIT

for row in "${MATRIX[@]}"; do
  IFS='|' read -r model variants max_tokens <<<"$row"
  wanted "$model" "$@" || continue
  echo "### $model: $variants ($(date))"
  "$LMS" unload --all
  "$LMS" load "$model" --context-length "$CONTEXT" -y
  if [[ $variants == *hybrid* ]]; then
    # A larger context makes LM Studio ask Metal for a buffer it can't get.
    "$LMS" load "$EMBED" --context-length 2048 -y
  fi
  DEP_WATCH_LLM_MAX_TOKENS=${max_tokens:-${DEP_WATCH_LLM_MAX_TOKENS:-2048}} \
    uv run python scripts/eval/run_variants.py "$model" "$variants" \
    --dataset "eval/datasets/$DATASET"
done

judged=()
for run in "${JUDGED[@]}"; do
  [[ -f $RUNS/$run.json ]] && judged+=("$RUNS/$run.json")
done
if ((${#judged[@]})); then
  echo "### judge $JUDGE ($(date))"
  "$LMS" unload --all
  "$LMS" load "$JUDGE" --context-length "$CONTEXT" -y
  DEP_WATCH_JUDGE_MODEL=$JUDGE uv run python scripts/eval/judge.py "${judged[@]}"
fi

if [[ -n ${LANGFUSE_PUBLIC_KEY:-} ]]; then
  replayed=()
  while IFS= read -r path; do replayed+=("$path"); done \
    < <(find "$RUNS" -name '*.json' -newer "$started" | sort)
  if ((${#replayed[@]})); then
    echo "### replay to Langfuse ($(date))"
    uv run python scripts/eval/replay.py "${replayed[@]}"
  fi
fi
echo "### done ($(date))"
