#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

python data/synthetic_planes.py --output data/plane_registration.json
python method/grassmann.py \
  --input data/plane_registration.json \
  --output checkpoints/grassmann_refine.json
bash scripts/evaluate.sh
