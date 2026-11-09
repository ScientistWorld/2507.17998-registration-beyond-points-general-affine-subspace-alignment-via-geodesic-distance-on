#!/bin/bash
# Run the paper's method (affine-Grassmannian plane registration) on the
# visible instances and score it into scoring/scores.json.
# The method needs no training; its solver is scripts/solvers/grassmann_refine.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/evaluate.sh grassmann_refine
