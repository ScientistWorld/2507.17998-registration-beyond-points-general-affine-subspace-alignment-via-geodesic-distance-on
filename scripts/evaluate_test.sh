#!/bin/bash
# Hidden test.  Run with no arguments.
#
# eval/test/evaluate.py generates the held-out registration instances (their
# seed exists only in eval/test/), runs every solver registered in
# scripts/solvers/ on the instance inputs alone, validates every returned pose
# and writes scoring/scores_test.json.  Nothing a method writes is trusted:
# every number is recomputed from the returned rotations and translations.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON:-python3}"
mkdir -p scoring
exec "${PYTHON_BIN}" eval/test/evaluate.py --output scoring/scores_test.json "$@"
