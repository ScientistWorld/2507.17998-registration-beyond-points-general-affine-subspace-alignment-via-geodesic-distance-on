#!/bin/bash
# Run the signed plane-parameter least-squares baseline on the visible
# instances and score it into scoring/scores.json.
# Its solver is scripts/solvers/plane_parameter_lstsq.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/evaluate.sh plane_parameter_lstsq
