# Scientist Constraints

## Data

The registration instances come from `data/synthetic_planes.py` (13 planes,
100 points per plane, noise sigma 0.05, outlier points uniform in a cube of
side 20, RANSAC plane fitting) with the experiment definitions in
`eval/train/evaluate.py`.  The hidden test generates its own instances from the
same distribution with a seed that only it holds, using its own frozen copy of
the generator: editing `data/` changes nothing on the test side.  You may
generate as many visible instances as you like for development.

## Solver contract

A method is a script `scripts/solvers/<name>.sh <problems.json> <predictions.json>`.
It receives only the instance inputs (`source`, `target`,
`target_signed_parameters`) and must return, for every instance id, a finite
proper rotation matrix (`||R^T R - I||_F <= 1e-6`, `det R > 0`) and a finite
translation.  A crash, a timeout (3 h for the whole suite), a missing instance
or any invalid pose fails the whole run (worst score on every metric).  No
self-reported number in the predictions file is read.

## Evaluation

Scores come only from the evaluators (`scripts/evaluate.sh`,
`scripts/evaluate_train.sh`, and the hidden `scripts/evaluate_test.sh`, which
takes no arguments).  The method must not import from or read `eval/`, the
evaluators' ground truth, or their seeds, and must not modify `eval/`,
`scoring/` or other solvers.  Every registered solver sees identical instances.

## Problem formulation

The task stays rigid 3D plane-to-plane registration from the given paired
plane features.  Raw point measurements are not available and must not be
reconstructed from generator internals; adding correspondences, changing the
number of planes, the noise, the outlier ratios, or the experiment sizes
changes the problem being measured.

## Compliance checklist

- [ ] The solver reads only its `problems.json` input (no `eval/`, no truths, no seeds)
- [ ] Every instance gets a finite rotation in SO(3) and a finite translation
- [ ] Instance distribution, experiment definitions and sizes are unchanged
- [ ] Scores are produced by the provided evaluators only
- [ ] The task remains paired rigid plane-to-plane registration
