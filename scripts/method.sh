#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user
PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" data/synthetic_planes.py --output data/plane_registration.json
"${PYTHON_BIN}" method/grassmann.py \
  --input data/plane_registration.json \
  --output checkpoints/grassmann_refine.json
bash scripts/evaluate.sh
