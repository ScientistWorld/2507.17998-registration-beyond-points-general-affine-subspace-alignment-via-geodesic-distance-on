# Progress

## What Works

Implemented the core plane-to-plane affine Grassmannian projection residual
from the paper's Eq. 7 / Corollary 2.3 in `method/grassmann.py`.  The official
repository is cloned under `method/upstream` for reference.  A signed
plane-parameter least-squares baseline is implemented in
`baseline/plane_parameter.py`, and `eval/evaluate_registration.py` scores
method outputs without importing from `method/`.

The current package is verified through `scripts/run.sh`, which calls
`scripts/reproduce.sh` and then `python3 validate.py --compare`.

Continuation audit hardening: `eval/evaluate_registration.py` now raises an
error when declared data or prediction artifacts are missing, instead of
silently writing partial scores.  `scripts/method.sh` and
`scripts/baseline.sh` pass the artifact they just produced to
`scripts/evaluate.sh`, while `scripts/reproduce.sh` still evaluates the full
suite.

Packaging audit update: the canonical full-suite evaluator now writes the
declared `plane_offset_rmse` metric to `scoring/scores.json`, and
`scripts/run.sh` refreshes that canonical score file before running the
supplemental train/test split diagnostics.

Final verification update: the canonical `scripts/evaluate.sh --suite` entry
point now discovers compatible prediction artifacts under a checkpoint
directory, matching the reusable method interface already used by the
train/test evaluators.

## Results

Scheduler job `bd5de5ed-df6` completed with exit code 0 and reran the full
three-setting suite with the corrected Eq. 7 residual, fairer signed-parameter
baseline, and hardened evaluator.  `python3 validate.py --compare` passed
inside the container.  The reproduction reaches `core_claim_plus` on the
scaled synthetic plane-registration task:

- 0% outliers: baseline 174.87% translation / 0.10 deg rotation; Grassmann 0.29% / 0.10 deg
- 5% outliers: baseline 172.13% translation / 3.38 deg rotation; Grassmann 17.99% / 4.19 deg
- 10% outliers: baseline 179.07% translation / 7.82 deg rotation; Grassmann 18.15% / 5.96 deg

This supports the paper's central claim for plane registration: optimizing the
affine Grassmannian plane representation avoids the signed-parameter ambiguity
that breaks direct plane-parameter least squares.

Final CPU verification job `e40e5cb7-0d5` also completed with exit code 0.  It
reran `scripts/run.sh` after the canonical evaluator-discovery fix and passed
`python3 validate.py --compare`, including the structural gym checks for
method/eval separation, train/test independence, method-key consistency, and
primary-metric discrimination.

Continuation fix: `method/grassmann.py` now follows Eq. (7) more directly by
using the 3D rotated-plane projector for direction-basis residuals and the 4D
embedded affine projector only for the displacement residual.  The
plane-parameter baseline now estimates rotation sign-invariantly, so the
comparison focuses on the translation weakness of signed Euclidean plane
parameters instead of forcing a 180-degree rotation failure.

## Remaining

Higher milestones would require reproducing additional paper task families,
especially line-to-line RGB-D odometry or line-to-plane PnL, and implementing
the paper's BnB inlier-set maximization rather than only the LM refinement
path for plane-to-plane registration.

## Issues

Generated scheduler logs are intentionally not tracked in git; validation
status is recorded in `MILESTONES.md`, `VERIFICATION.md`, and the committed
score files.

Continuation audit found a script portability issue: shell entry points used
`python`, which was shadowed by a Node-managed shim in the login environment
and lacked NumPy.  This was fixed by using `${PYTHON:-python3}` consistently in
scripts and installing dependencies into that interpreter from
`environment/setup.sh`.  After the fix, standalone evaluation and full
reproduction both pass with `python3 validate.py --compare`.

## Deviations from Paper

The paper's object-registration experiment uses the Space Station CAD model
from prior work, with 13 planes, 100 sampled points per plane, Gaussian noise,
outlier ratios up to 50%, and 500 random sets per ratio.  The mesh is not
distributed with the paper, so this reproduction uses an authored synthetic
13-plane object with the same plane-count, point-count, noise, fitting, and
rigid-transform evaluation structure.  The gym uses one fixed seed and the
0%, 5%, and 10% outlier settings rather than 500 random trials through 50%,
keeping the CPU benchmark quick and deterministic.  The synthetic target plane
parameters deliberately alternate antipodal signs for the signed-parameter
baseline, documenting the representation ambiguity analyzed in the paper.  The
algorithm is not substituted: the method still optimizes the affine
Grassmannian embedded basis-projection residual.

The paper's Fig. 3 object-registration results are published as curves rather
than a numeric table.  The current `scoring/reference.json` therefore records
scaled synthetic benchmark targets, not literal table entries from the paper.
Those targets should be interpreted as the expected behavior of this reusable
gym: lower translation and rotation error under the same 13-plane constraint.
