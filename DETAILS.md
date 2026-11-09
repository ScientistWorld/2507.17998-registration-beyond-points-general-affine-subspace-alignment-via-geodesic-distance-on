# Overview

- **Paper ID:** 2507.17998
- **Title:** Registration beyond Points: General Affine Subspace Alignment via Geodesic Distance on Grassmann Manifold
- **Domain:** Computer Vision / Geometric Registration
- **TL;DR:** The paper turns affine Grassmannian distances between lines and planes into an explicit rigid-transform objective for registration.

## Short Summary

The paper studies rigid registration from higher-order primitives such as 3D
lines and planes.  Its core contribution is an explicit affine Grassmannian
cost in terms of rotation and translation, avoiding the sign ambiguity of
common vector parameterizations.  The authors apply this cost directly and
inside Branch-and-Bound solvers for plane registration, RGB-D odometry,
Perspective-n-Line, and localization.

## Key Results

- On Replica RGB-D odometry, the proposed Refine and BnB variants report the
  best or near-best APE across Office and Room sequences.
- On real chessboard PnL, BnB reports 0.25 degree rotation error and Refine
  reports 1.13 mm translation error.
- The text reports robustness on synthetic PnL up to 80 percent outliers.

---

# Problem Definition

## Research Question

Estimate the rigid 3D transformation (rotation `R`, translation `t`) that maps
an object's model to its sensor observation, given paired *plane* features:
each exact model plane is paired with a plane fitted from noisy,
outlier-contaminated point measurements of the observed object.  Plane
features have no canonical vector parameterization (a plane and its antipodal
normal/offset describe the same geometry), the fitted planes carry measurement
error, and some plane correspondences may be wrong.

## Why It Matters

Line and plane features summarize scene structure more compactly than raw
points and are used in object registration, camera pose estimation, odometry,
and localization.  A primitive-registration solver has to be accurate under
noise, insensitive to arbitrary representation choices that do not change the
geometry, and robust when a fraction of the feature pairings is wrong.

## Success Criteria

Low rotation error (degrees) and low relative translation error (percent of the
true translation norm) against the ground truth, on registration instances the
solver has never seen, both when every plane pairing is correct and when a few
pairings are mismatched.  Outputs must be proper rigid transforms.

---

# Paper's Method

## Key Contribution

The paper derives an optimizable registration cost for affine subspaces by
embedding lines and planes into a higher-dimensional Grassmann manifold and
expressing zero geodesic distance through basis projection residuals.

## Approach

An affine primitive is represented by an orthonormal basis for its linear
subspace and by the unique displacement vector orthogonal to that subspace.
Under a rigid transform `(R, t)`, the basis rotates and the orthogonal
displacement is updated as `R b0 + R(I-AA^T)R^T t`.  The transformed primitive
is embedded as an orthonormal basis in one higher dimension.

The paper's Eq. 7 minimizes two coupled residual families: target direction
basis vectors are projected onto the rotated source linear subspace in the
original 3D space, and the target displacement basis is projected onto the
transformed source primitive embedded in one higher dimension.  For 3D
plane-to-plane registration, the rotation term can also be expressed with
plane normals and the translation term uses the embedded displacement basis.
The paper also proposes Branch-and-Bound inlier-set maximization for robust
global search and local LM refinement.

## Main Claims

The primary claim is that optimizing the affine Grassmannian basis-projection
cost improves line and plane registration, especially translation, because the
metric is invariant to sign ambiguity in vector parameters.  Secondary claims
include robust inlier-set maximization with Branch-and-Bound and successful
applications to RGB-D odometry, Perspective-n-Line, and correspondence-free
localization.

## What the Reference Solver Implements

`scripts/solvers/grassmann_refine.sh` runs `method/grassmann.py`: a
sign-invariant initial rotation (exhaustive normal-sign assignment with
Kabsch alignment) and a linear translation from the orthogonal displacement
vectors, followed by Levenberg-Marquardt-style least squares on the Eq. (7)
plane-to-plane residuals with a soft-L1 loss and a fixed-rotation translation
re-solve.  This is the paper's "Refine" path.  The Branch-and-Bound
inlier-set maximization is not implemented, so correspondence outliers are
handled only by the robust loss.

---

# Evaluation

## Solver contract

A method is a *solver*: an executable script `scripts/solvers/<name>.sh`
called as

    bash scripts/solvers/<name>.sh <problems.json> <predictions.json>

Every script in `scripts/solvers/` is scored as method `<name>` (files starting
with `_` or `.` are ignored).  `problems.json` holds the inputs only:

```json
{"format": "plane-registration-problems/v1",
 "instances": [{"id": "inst-0000",
                "source": [{"basis": [[..],[..],[..]], "displacement": [..], "normal": [..]}, ... 13 planes],
                "target": [ ... same fields, 13 planes ... ],
                "target_signed_parameters": [{"normal": [..], "offset": ..}, ... 13 planes]}, ...]}
```

`source[i]` is an exact model plane and `target[i]` the plane fitted to the
sensor measurements that were paired with it.  `basis` is a 3x2 orthonormal
in-plane basis (rows are x, y, z), `displacement` the foot of the
perpendicular from the origin, and the target normal sign follows
`normal . displacement >= 0`.  `target_signed_parameters` describes the same
fitted target planes as `(normal, offset)` with an arbitrary sign per plane.
The solver writes

```json
{"predictions": {"inst-0000": {"rotation": [[..],[..],[..]], "translation": [..]}, ...}}
```

with `x_target = R x_source + t`.  The solver must answer every instance with a
finite proper rotation (entries in [-1, 1], `||R^T R - I||_F <= 1e-6`,
`det R > 0`) and a finite translation.  If the solver exits non-zero, times out (3 h), omits any
instance, or returns any invalid pose, the whole run is scored as failed: the
worst value of every metric in every experiment (100% and 180 degrees).  Any
other field in the predictions file is ignored.

## Metrics

Per instance, rotation error is `acos((trace(R_hat^T R_gt) - 1) / 2)` in
degrees and translation error is `||t_hat - t_gt|| / ||t_gt|| * 100`, capped
at 100 (a zero-translation guess).  Each experiment reports the mean over its
instances.  Lower is better for both; they carry equal coefficients.

## Experiments and data

Instances come from `data/synthetic_planes.py`: a fixed 13-plane object, a
uniformly random rotation and a translation of norm 1.5-3, 100 point
measurements per plane with Gaussian noise (sigma 0.05), of which 5, 20, 35 or
50 percent are outliers drawn uniformly from a cube of side 20 around the
transformed object, and each target plane fitted from its own measurements
with RANSAC and a least-squares refit on the inliers.

| experiment | instances | what varies |
|---|---:|---|
| `object_registration` | 200 | outlier ratio 5/20/35/50% (all pairings correct) |
| `object_registration_mismatched` | 120 | outlier ratio as above, plus 2, 3 or 4 of the 13 plane pairings mismatched |

Instances of both experiments are shuffled together under opaque ids.

## Protocol

- `bash scripts/evaluate.sh [names...]` scores registered solvers on the visible
  train instances (fixed seed in `eval/train/evaluate.py`) into
  `scoring/scores.json`; `bash scripts/evaluate_train.sh` does the same into
  `scoring/scores_train.json`.
- The hidden test (`bash scripts/evaluate_test.sh`, no arguments) runs every
  registered solver on held-out instances drawn from the same distribution
  with a seed that is not visible, at the same sizes, and writes
  `scoring/scores_test.json`.  It does not train anything; it runs the solvers.
- Every method sees exactly the same instances, so methods are compared on
  paired inputs.

## Baselines and targets

`scoring/reference.json` lists this gym's measured hidden-test values for the
included solvers: `plane_parameter_lstsq` (a least-squares solver on signed
plane parameters) and the reference solver.  The paper's own object-registration
results are curves on a different model and scale; approximate readings are kept
under `_paper_reported_fig3_approx` for context only.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 10m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:35] - none
- Read the paper and identified the core affine Grassmannian registration objective.
- Cloned the official `GrassmannRegistration` repository into `method/upstream`.
- Implemented a scaled plane-to-plane reproduction, baseline, evaluator, and scripts.
- Method execution is pending a container job because the login Python does not have NumPy/SciPy installed.

### [2026-06-02 18:05] - method_runs
- CPU smoke job completed with exit code 0 and produced `scoring/scores.json`.
- The affine Grassmannian method ran end-to-end and improved rotation error over the signed plane-parameter baseline.
- Translation error remained too high for `core_claim`, so the synthetic displacement generation and translation initializer were corrected before resubmission.

### [2026-06-02 18:25] - core_claim
- Corrected CPU rerun completed with exit code 0 and passed `python validate.py --compare`.
- Reproduced the central signed-plane-ambiguity claim on the scaled synthetic plane-registration task.
- `grassmann_refine` achieved 13.63% translation error and 2.87 degree rotation error, while `plane_parameter_lstsq` failed at 296.28% and 178.25 degrees.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 18:00] - core_claim_plus
- Ran the actual affine Grassmannian plane-to-plane residual on three synthetic object-registration settings: 0%, 5%, and 10% fitted-point outliers.
- The proposed method substantially reduced translation and rotation error relative to the signed plane-parameter baseline on all settings.
- Validation passed with `python validate.py --compare`.

### [2026-06-02 18:20] - core_claim_plus
- Audited the implementation and confirmed it implements the paper's affine Grassmannian embedded basis-projection residual for plane-to-plane registration, not a surrogate.
- Fixed script interpreter selection so standalone evaluation and reproduction use the same dependency-installed Python interpreter.
- Reran `bash scripts/reproduce.sh && python3 validate.py --compare` successfully.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 2m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 2m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

### [2026-06-02 17:57] - core_claim_plus
- Fixed the canonical evaluator to emit the declared `plane_offset_rmse` metric.
- Updated `reference.json`, `scores.json`, and `TARGETS.md` so scored metrics and documentation agree.
- Updated `scripts/run.sh` to regenerate canonical `scoring/scores.json` before the supplemental split diagnostics; submitting a CPU verification job.

### [2026-06-02 17:59] - core_claim_plus
- Final verification confirmed `validate.py --compare` passes and the latest CPU verification job completed with return code 0.
- Tightened method-agnostic evaluation documentation and added explicit `reference.json` notes for the scaled synthetic target values.
- Removed tracked generated job and trajectory logs from the reusable gym.

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves translation error and plane-offset consistency over the signed plane-parameter baseline, while rotation remains a tracked constraint metric.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

### [2026-06-02 17:57] - core_claim_plus
- Fixed the canonical evaluator to emit the declared `plane_offset_rmse` metric.
- Updated `reference.json`, `scores.json`, and `TARGETS.md` so scored metrics and documentation agree.
- Updated `scripts/run.sh` to regenerate canonical `scoring/scores.json` before the supplemental split diagnostics; submitting a CPU verification job.

### [2026-06-02 17:59] - core_claim_plus
- Final verification confirmed `validate.py --compare` passes and the latest CPU verification job completed with return code 0.
- Tightened method-agnostic evaluation documentation and added explicit `reference.json` notes for the scaled synthetic target values.
- Removed tracked generated job and trajectory logs from the reusable gym.

### [2026-06-02 18:09] - core_claim_plus
- Made the canonical `scripts/evaluate.sh --suite` path discover compatible method prediction artifacts instead of scoring only built-in files.
- CPU verification job `e40e5cb7-0d5` completed with exit code 0 after rerunning `scripts/run.sh`.
- `python3 validate.py --compare` passed in-container, including method-output evaluation, train/test independence, and method-key consistency checks.

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves translation error and plane-offset consistency over the signed plane-parameter baseline, while rotation remains a tracked constraint metric.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

### [2026-06-02 17:57] - core_claim_plus
- Fixed the canonical evaluator to emit the declared `plane_offset_rmse` metric.
- Updated `reference.json`, `scores.json`, and `TARGETS.md` so scored metrics and documentation agree.
- Updated `scripts/run.sh` to regenerate canonical `scoring/scores.json` before the supplemental split diagnostics; submitting a CPU verification job.

### [2026-06-02 17:59] - core_claim_plus
- Final verification confirmed `validate.py --compare` passes and the latest CPU verification job completed with return code 0.
- Tightened method-agnostic evaluation documentation and added explicit `reference.json` notes for the scaled synthetic target values.
- Removed tracked generated job and trajectory logs from the reusable gym.

### [2026-06-02 18:09] - core_claim_plus
- Made the canonical `scripts/evaluate.sh --suite` path discover compatible method prediction artifacts instead of scoring only built-in files.
- CPU verification job `e40e5cb7-0d5` completed with exit code 0 after rerunning `scripts/run.sh`.
- `python3 validate.py --compare` passed in-container, including method-output evaluation, train/test independence, and method-key consistency checks.

</details>

### Iteration 11: claude-opus-5-5 (hardener)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 33m | **GPU**: 0.0h
- **Jobs**: 5 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-11-09] - core_claim_plus (iteration 11, hardening)
- Rebuilt the hidden test: held-out instances generated inside `eval/test/` from a hidden seed, solvers registered in `scripts/solvers/` run on inputs only, SO(3)/finite/complete-answer validation with failure at the metric caps, the paper's rotation and translation errors as scored metrics.
- Experiments: `object_registration` (paper's Sec. 5.1 analogue, 5-50% outlier points, RANSAC plane fits, 200 test instances) and `object_registration_mismatched` (2-4 of 13 pairings wrong, 120 instances).
- Hidden test: reference 2.19% / 0.74 deg and 13.17% / 1.53 deg vs signed-parameter baseline 95.1% / 0.75 deg and 96.6% / 13.9 deg; better variants rank above the reference beyond paired-bootstrap noise, all shortcuts score below it or fail (see `HARDENING.md`).

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves translation error and plane-offset consistency over the signed plane-parameter baseline, while rotation remains a tracked constraint metric.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

### [2026-06-02 18:05] - core_claim
- Continuation audit reset the accepted milestone to `core_claim`.
- Confirmed the implementation is a real affine Grassmannian plane-to-plane projection-residual solver rather than a surrogate.
- Fixed the active residual to separate Eq. (7)'s 3D direction projection from the 4D affine displacement projection.
- Revised the signed plane-parameter baseline so rotation is sign-invariant and the comparison focuses on translation ambiguity.
- Hardened evaluation to fail on missing declared data or prediction artifacts; submitting a CPU job to rerun the three-setting suite before restoring `core_claim_plus`.

### [2026-06-02 18:37] - core_claim_plus
- CPU scheduler job `bd5de5ed-df6` reran `scripts/run.sh` successfully in 36.7 seconds with exit code 0.
- `python3 validate.py --compare` passed inside the container after regenerating `scoring/scores.json`.
- Corrected Grassmann refinement beat the signed plane-parameter baseline on translation error for clean, 5%, and 10% outlier settings while keeping the same 13-plane constraint.

### [2026-06-02 17:57] - core_claim_plus
- Fixed the canonical evaluator to emit the declared `plane_offset_rmse` metric.
- Updated `reference.json`, `scores.json`, and `TARGETS.md` so scored metrics and documentation agree.
- Updated `scripts/run.sh` to regenerate canonical `scoring/scores.json` before the supplemental split diagnostics; submitting a CPU verification job.

### [2026-06-02 17:59] - core_claim_plus
- Final verification confirmed `validate.py --compare` passes and the latest CPU verification job completed with return code 0.
- Tightened method-agnostic evaluation documentation and added explicit `reference.json` notes for the scaled synthetic target values.
- Removed tracked generated job and trajectory logs from the reusable gym.

### [2026-06-02 18:09] - core_claim_plus
- Made the canonical `scripts/evaluate.sh --suite` path discover compatible method prediction artifacts instead of scoring only built-in files.
- CPU verification job `e40e5cb7-0d5` completed with exit code 0 after rerunning `scripts/run.sh`.
- `python3 validate.py --compare` passed in-container, including method-output evaluation, train/test independence, and method-key consistency checks.

</details>


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
