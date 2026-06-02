# Progress

## What Works

Implemented the core plane-to-plane affine Grassmannian projection residual
from the paper's Eq. 7 / Corollary 2.3 in `method/grassmann.py`.  The official
repository is cloned under `method/upstream` for reference.  A signed
plane-parameter least-squares baseline is implemented in
`baseline/plane_parameter.py`, and `eval/evaluate_registration.py` scores
method outputs without importing from `method/`.

## Results

The corrected CPU rerun completed successfully and passed
`python validate.py --compare`.  The reproduction reaches `core_claim` on the
scaled synthetic plane-registration task:

- `plane_parameter_lstsq`: 178.25 degree rotation error, 296.28% translation error
- `grassmann_refine`: 2.87 degree rotation error, 13.63% translation error

This supports the paper's central claim for plane registration: optimizing the
affine Grassmannian plane representation avoids the signed-parameter ambiguity
that breaks direct plane-parameter least squares.

## Remaining

Higher milestones would require expanding beyond the minimum synthetic setting,
for example sweeping outlier ratios or reproducing the paper's line-to-plane
and line-to-line experiments.

## Issues

The scheduler-provided stdout/stderr paths for both completed jobs were not
visible from this container, but each job reported exit code 0 and wrote the
expected workspace artifacts.  Validation was rerun locally with
`python validate.py --compare`.

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
