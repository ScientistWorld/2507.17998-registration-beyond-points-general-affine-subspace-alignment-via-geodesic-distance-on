# Progress

## What Works

Implemented the core plane-to-plane affine Grassmannian projection residual
from the paper's Eq. 7 / Corollary 2.3 in `method/grassmann.py`.  The official
repository is cloned under `method/upstream` for reference.  A signed
plane-parameter least-squares baseline is implemented in
`baseline/plane_parameter.py`, and `eval/evaluate_registration.py` scores
method outputs without importing from `method/`.

The current package is ready for a CPU reproducibility check through
`scripts/run.sh`, which calls `scripts/reproduce.sh` and then
`python3 validate.py --compare`.

## Results

The expanded CPU rerun completed successfully and passed
`python validate.py --compare`.  The reproduction reaches `core_claim_plus` on
the scaled synthetic plane-registration task:

- 0% outliers: baseline 329.69% translation / 179.80 deg rotation; Grassmann 0.37% / 0.15 deg
- 5% outliers: baseline 296.28% translation / 178.25 deg rotation; Grassmann 13.63% / 2.87 deg
- 10% outliers: baseline 282.02% translation / 174.85 deg rotation; Grassmann 22.65% / 8.56 deg

This supports the paper's central claim for plane registration: optimizing the
affine Grassmannian plane representation avoids the signed-parameter ambiguity
that breaks direct plane-parameter least squares.

## Remaining

Higher milestones would require reproducing additional paper task families,
especially line-to-line RGB-D odometry or line-to-plane PnL, and implementing
the paper's BnB inlier-set maximization rather than only the LM refinement
path for plane-to-plane registration.

Continuation audit: the workspace is internally consistent at
`core_claim_plus`; the next action is a CPU job submission to verify the
packaged suite in the scheduler container.

## Issues

The scheduler-provided stdout/stderr paths for both completed jobs were not
visible from this container, but each job reported exit code 0 and wrote the
expected workspace artifacts.  Validation was rerun locally with
`python validate.py --compare`.

Continuation audit found a script portability issue: shell entry points used
`python`, which was shadowed by a Node-managed shim in the login environment
and lacked NumPy.  This was fixed by using `${PYTHON:-python3}` consistently in
scripts and installing dependencies into that interpreter from
`environment/setup.sh`.  After the fix, standalone evaluation and full
reproduction both pass with `python3 validate.py --compare`.

## Deviations from Paper

The paper's object-registration experiment uses the Space Station CAD model
from prior work, with 13 planes, 100 sampled points per plane, Gaussian noise,
and outliers.  The mesh is not distributed with the paper, so this reproduction
uses an authored synthetic 13-plane object with the same plane-count,
point-count, noise, fitting, and rigid-transform evaluation structure.  The
minimum core-claim setting uses 5% fitted-point outliers to keep the synthetic
plane estimates non-trivial without making the first reproduction dominated by
plane-fitting breakdown.  The expanded suite also includes 0% and 10% outlier
settings.  The algorithm is not substituted: the method still optimizes the
affine Grassmannian embedded basis-projection residual.
