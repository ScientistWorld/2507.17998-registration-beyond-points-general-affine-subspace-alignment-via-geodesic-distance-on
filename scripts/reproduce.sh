#!/bin/bash
# Reproduce the gym's reference results end to end (CPU only, no training).
#
# 1. scoring/scores.json        every registered solver on the visible instances
# 2. scoring/scores_train.json  same, through the train entry point
# 3. scoring/scores_test.json   every registered solver on the hidden instances
#
# Registered solvers: scripts/solvers/grassmann_refine.sh (paper's method) and
# scripts/solvers/plane_parameter_lstsq.sh (signed-parameter baseline).
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/evaluate.sh
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
