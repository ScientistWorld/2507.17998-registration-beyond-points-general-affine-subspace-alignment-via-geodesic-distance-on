#!/bin/bash
# Registered solver: signed plane-parameter least-squares baseline.
# Contract: bash scripts/solvers/<name>.sh <problems.json> <predictions.json>
set -euo pipefail
cd "$(dirname "$0")/../.."
exec "${PYTHON:-python3}" baseline/plane_parameter.py --problems "$1" --predictions "$2"
