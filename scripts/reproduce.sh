#!/bin/bash
# Reproduce the paper's results end-to-end.
#
# This script runs inside the compute container and should call
# scripts/baseline.sh and scripts/method.sh to run baselines and
# the paper's method, each of which calls scripts/evaluate.sh.
#
# Assumes:
#   - Container is built (environment/container.sif)
#   - Data and models are downloaded (via scripts/download.sh)
#   - Working directory is /home/user
#
# This is the "gold standard" reproduction — 
# You do not need to run this, but keep this in good shape
# so other agents can easily run a full loop of reproduction and get the paper's numbers.

set -e

cd /home/user

for ratio in 0.00 0.05 0.10; do
  data_path="data/plane_registration_outlier_${ratio}.json"
  baseline_out="checkpoints/plane_parameter_lstsq_outlier_${ratio}.json"
  method_out="checkpoints/grassmann_refine_outlier_${ratio}.json"
  python data/synthetic_planes.py --outlier-ratio "${ratio}" --output "${data_path}"
  python baseline/plane_parameter.py --input "${data_path}" --output "${baseline_out}"
  python method/grassmann.py --input "${data_path}" --output "${method_out}"
done

cp data/plane_registration_outlier_0.05.json data/plane_registration.json
cp checkpoints/plane_parameter_lstsq_outlier_0.05.json checkpoints/plane_parameter_lstsq.json
cp checkpoints/grassmann_refine_outlier_0.05.json checkpoints/grassmann_refine.json

bash scripts/evaluate.sh --suite
