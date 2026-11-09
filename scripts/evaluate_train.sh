#!/bin/bash
# Visible train evaluation.  Same experiments, sizes, metrics and solver
# contract as the hidden test, on instances from the public generator
# (data/synthetic_planes.py) with a visible seed.  Writes
# scoring/scores_train.json.  Optional arguments: solver names to score
# (default: every solver registered in scripts/solvers/).
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON:-python3}"
mkdir -p scoring
exec "${PYTHON_BIN}" eval/train/evaluate.py --output scoring/scores_train.json "$@"
