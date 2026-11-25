#!/usr/bin/env bash
# The proposal's experiment matrix on LM Studio, from a clean checkout to the report:
#
#   1. preflight: LM Studio server up, every model downloaded, the database migrated
#      (hybrid retrieval stores passages in pgvector), the Langfuse keys set;
#   2. every model's variants, one model loaded at a time, so a run's latency is its own
#      model's and memory stays within 16 GB (RQ1: zeroshot vs direct; RQ2: fewshot, CoT and
#      4B vs 9B; RQ3: hybrid);
#   3. judged faithfulness for the Qwen3-4B runs (RQ3), skipping runs already judged;
#   4. the dataset uploaded and every new run recorded as a Langfuse experiment;
#   5. the comparison and error-analysis report over every run of the matrix, against the
#      Qwen3-4B zero-shot reference, in $DEP_WATCH_RUNS_DIR/<dataset>/report.md.
#
#   scripts/eval/run_matrix.sh                       # everything (several hours)
#   scripts/eval/run_matrix.sh qwen/qwen3.5-9b       # only the models named
#   VARIANTS=hybrid scripts/eval/run_matrix.sh qwen/qwen3-4b-2507
#   scripts/eval/run_matrix.sh --check               # preflight only
#   scripts/eval/run_matrix.sh --report              # the report only, from saved runs
#
# Overrides: ENV_FILE (default .env), LMS (the lms CLI), DATASET, JUDGE, VARIANTS,
# DEP_WATCH_RUNS_DIR (default eval/runs). Postgres: `docker compose up -d`.
set -euo pipefail
cd "$(dirname "$0")/../.."
ENV_FILE=${ENV_FILE:-.env}
if [[ -f $ENV_FILE ]]; then set -a; source "$ENV_FILE"; set +a; fi

LMS=${LMS:-$HOME/.lmstudio/bin/lms}
DATASET=${DATASET:-kafka-ground-truth-v2}
JUDGE=${JUDGE:-qwen/qwen3.5-9b}
EMBED=${DEP_WATCH_EMBED_MODEL:-text-embedding-qwen3-embedding-0.6b}
export DEP_WATCH_RUNS_DIR=${DEP_WATCH_RUNS_DIR:-eval/runs}
RUNS=$DEP_WATCH_RUNS_DIR/$DATASET
CONTEXT=16384

# model | variants | max output tokens (reasoning models think first) | where to download it
MATRIX=(
  "qwen/qwen3-4b-2507|zeroshot,fewshot,cot,direct,hybrid||qwen/qwen3-4b-2507"
  "google/gemma-4-e4b|zeroshot,fewshot,direct|8192|google/gemma-4-e4b"
  "qwen/qwen3.5-9b|zeroshot,fewshot,direct|8192|qwen/qwen3.5-9b"
  "meta-llama-3.1-8b-instruct|zeroshot,fewshot,direct||https://huggingface.co/mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
)
EMBED_SOURCE=https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF
REFERENCE=qwen3-4b-2507
# Judged runs (the judge is never the model under test).
JUDGED=(qwen3-4b-2507 qwen3-4b-2507-fewshot qwen3-4b-2507-hybrid)

mode=run
case ${1:-} in
  --check) mode=check; shift ;;
  --report) mode=report; shift ;;
esac
models=("$@")

wanted() {  # true if no model was named, or this one was
  ((${#models[@]} == 0)) && return 0
  for name in "${models[@]}"; do [[ $name == "$1" ]] && return 0; done
  return 1
}

run_names() {  # every run of the matrix's selected rows: <model>[-<variant>]
  for row in "${MATRIX[@]}"; do
    IFS='|' read -r model variants _ _ <<<"$row"
    wanted "$model" || continue
    local name=${model##*/}
    IFS=',' read -r -a list <<<"${VARIANTS:-$variants}"
    for v in "${list[@]}"; do
      if [[ $v == zeroshot ]]; then echo "$name"; else echo "$name-$v"; fi
    done
  done
}

preflight() {
  local missing=0 downloaded
  [[ -x $LMS ]] || { echo "no lms CLI at $LMS (install LM Studio, or set LMS)"; exit 1; }
  "$LMS" server start >/dev/null
  downloaded=$("$LMS" ls)
  for row in "${MATRIX[@]}" "$JUDGE|||$JUDGE" "$EMBED|||$EMBED_SOURCE"; do
    IFS='|' read -r model _ _ source <<<"$row"
    [[ $model == "$JUDGE" || $model == "$EMBED" ]] || wanted "$model" || continue
    if ! grep -qF "$model" <<<"$downloaded"; then
      echo "missing model $model: $LMS get $source"
      missing=1
    fi
  done
  ((missing == 0)) || exit 1
  uv run alembic upgrade head >/dev/null 2>&1 \
    || { echo "cannot migrate the database at DATABASE_URL (docker compose up -d?)"; exit 1; }
  if [[ -z ${LANGFUSE_PUBLIC_KEY:-} ]]; then
    echo "no LANGFUSE_PUBLIC_KEY: runs are saved locally only, not recorded in Langfuse"
  fi
  echo "preflight ok: models, database, LM Studio server"
}

report() {
  local runs=() reference=0 i=0
  for name in $(run_names); do
    [[ -f $RUNS/$name.json ]] || continue
    [[ $name == "$REFERENCE" ]] && reference=$i
    runs+=("$RUNS/$name.json")
    i=$((i + 1))
  done
  if ((${#runs[@]} == 0)); then echo "no saved runs in $RUNS"; return; fi
  uv run python -m dep_watch_agent.eval.analysis "eval/datasets/$DATASET" "${runs[@]}" \
    --reference "$reference" --out "$RUNS/report.md"
  echo "report: $RUNS/report.md (${#runs[@]} runs)"
}

if [[ $mode == report ]]; then report; exit 0; fi
preflight
if [[ $mode == check ]]; then exit 0; fi

started=$(mktemp)
trap 'rm -f "$started"; "$LMS" unload --all >/dev/null 2>&1 || true' EXIT

for row in "${MATRIX[@]}"; do
  IFS='|' read -r model variants max_tokens _ <<<"$row"
  wanted "$model" || continue
  variants=${VARIANTS:-$variants}
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
    echo "### record in Langfuse ($(date))"
    uv run python scripts/eval/replay.py --upload "${replayed[@]}"
  fi
fi

models=()  # the report covers every run of the matrix, not only this invocation's
VARIANTS=
report
echo "### done ($(date))"
