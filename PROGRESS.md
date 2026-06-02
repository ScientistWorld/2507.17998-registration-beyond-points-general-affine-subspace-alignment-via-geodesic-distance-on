# Progress

## What Works

Implemented the core plane-to-plane affine Grassmannian projection residual
from the paper's Eq. 7 / Corollary 2.3 in `method/grassmann.py`.  The official
repository is cloned under `method/upstream` for reference.  A signed
plane-parameter least-squares baseline is implemented in
`baseline/plane_parameter.py`, and `eval/evaluate_registration.py` scores
method outputs without importing from `method/`.

## Results

No reproduced scores yet.  A CPU test job is being submitted to install the
declared NumPy/SciPy dependencies in the container and run `scripts/reproduce.sh`.

## Remaining

Run the container job, inspect `scoring/scores.json`, and iterate if the
Grassmann residual does not improve translation error over the parameter
baseline.  After a successful run, update the milestone to `method_runs` or
`core_claim` depending on the measured gap.

## Issues

The login-node Python environment lacks NumPy and SciPy.  Dependencies are
declared in `environment/setup.sh`; actual validation must run in the managed
container rather than by installing packages locally.

## Deviations from Paper

The paper's object-registration experiment uses the Space Station CAD model
from prior work, with 13 planes, 100 sampled points per plane, Gaussian noise,
and outliers.  The mesh is not distributed with the paper, so this reproduction
uses an authored synthetic 13-plane object with the same plane-count,
point-count, noise, fitting, and rigid-transform evaluation structure.  The
algorithm is not substituted: the method still optimizes the affine
Grassmannian embedded basis-projection residual.
