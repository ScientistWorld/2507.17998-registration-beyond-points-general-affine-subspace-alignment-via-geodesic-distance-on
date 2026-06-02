# Scientist Constraints

## Data

Use the generated `data/plane_registration.json` problem with the default
settings from `data/synthetic_planes.py`: 13 planes, 100 sampled points per
plane, noise sigma 0.05, 5 percent outlier-corrupted target samples, and seed
7.  Increasing the number of planes, lowering the noise, changing the seed to a
more favorable instance, or using the ground-truth transform during estimation
is resource or data leakage rather than methodological improvement.

## Evaluation

Predictions must be written as rigid transforms in the same JSON format under
`checkpoints/` and scored only through `scripts/evaluate.sh`.  The evaluator
must not import from `method/`, and the method must not modify
`data/plane_registration.json` after prediction.

## Problem Formulation

The task must remain rigid 3D plane-to-plane registration from paired affine
plane features.  Converting the task to point-cloud ICP over all sampled points
or adding extra correspondences changes the problem being measured.

## Compliance Checklist

- [ ] Default synthetic dataset settings are unchanged
- [ ] Number of plane correspondences remains 13
- [ ] Ground-truth rotation and translation are not used by the estimator
- [ ] Scores are produced by `scripts/evaluate.sh`
- [ ] The task remains paired rigid plane-to-plane registration
