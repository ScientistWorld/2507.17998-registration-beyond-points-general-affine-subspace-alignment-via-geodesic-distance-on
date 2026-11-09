#!/bin/bash
# Registered solver: the paper's affine-Grassmannian plane registration (reference).
#
# Solver contract (every scripts/solvers/<name>.sh is scored as method <name>):
#   bash scripts/solvers/<name>.sh <problems.json> <predictions.json>
# Read {"instances": [{"id", "source", "target", "target_signed_parameters"}]}
# and write {"predictions": {<id>: {"rotation": 3x3, "translation": [3]}}}.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON:-python3}" method/grassmann.py --problems "$1" --predictions "$2"
