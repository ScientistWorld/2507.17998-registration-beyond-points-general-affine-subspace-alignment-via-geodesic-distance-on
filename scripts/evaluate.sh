#!/bin/bash
# Standard evaluation of this environment (visible instances).
#
# Runs every solver registered in scripts/solvers/ (or only the solver names
# given as arguments) on the visible train instances and writes
# scoring/scores.json, nested as experiments -> results -> method -> metrics
# with the experiment and metric names of scoring/reference.json.
#
# Solver contract: bash scripts/solvers/<name>.sh <problems.json> <predictions.json>
#
# Examples:
#   bash scripts/evaluate.sh                    # every registered solver
#   bash scripts/evaluate.sh grassmann_refine   # one solver
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON:-python3}"
mkdir -p scoring
exec "${PYTHON_BIN}" eval/train/evaluate.py --output scoring/scores.json "$@"
