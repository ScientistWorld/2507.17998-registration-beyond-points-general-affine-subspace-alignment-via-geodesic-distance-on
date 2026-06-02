# Progress

## What Works

Implemented the core plane-to-plane affine Grassmannian projection residual
from the paper's Eq. 7 / Corollary 2.3 in `method/grassmann.py`.  The official
repository is cloned under `method/upstream` for reference.  A signed
plane-parameter least-squares baseline is implemented in
`baseline/plane_parameter.py`, and `eval/evaluate_registration.py` scores
method outputs without importing from `method/`.

## Results

The first CPU smoke job completed successfully and wrote `scoring/scores.json`.
It established `method_runs`: the Grassmann residual executes end-to-end in the
container and improves rotation over the signed plane-parameter baseline.

The initial translation result was still too weak for `core_claim`
(`grassmann_refine`: 14.87 deg rotation error, 150.67% translation error;
`plane_parameter_lstsq`: 139.28 deg, 267.76%).  Inspecting the synthetic data
generator revealed that target plane displacements used the tangential
translation component rather than the affine Grassmann plane-transform
component.  The generator and translation initializer have been corrected and a
second CPU job is being submitted.

## Remaining

Run the corrected container job, inspect `scoring/scores.json`, and claim
`core_claim` only if the method produces a clearly better translation and
rotation estimate than the signed plane-parameter baseline.

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
minimum core-claim setting uses 5% fitted-point outliers to keep the synthetic
plane estimates non-trivial without making the first reproduction dominated by
plane-fitting breakdown.  The algorithm is not substituted: the method still
optimizes the affine Grassmannian embedded basis-projection residual.
