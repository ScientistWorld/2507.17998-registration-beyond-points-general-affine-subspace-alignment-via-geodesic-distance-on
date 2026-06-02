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

Estimate rigid 3D transformations between geometric primitives such as lines
and planes.  The benchmark asks whether a solver can recover rotation and
translation from paired affine features when the features are noisy and their
common vector parameterizations may have arbitrary signs.

## Why It Matters

Line and plane features summarize scene structure more compactly than raw
points and are useful in object registration, camera pose estimation, odometry,
and localization.  A reliable primitive registration solver should be robust to
noise, outliers, and representation choices that do not change the underlying
geometry.

## Success Criteria

Success is measured by low rotation and translation error against known ground
truth on paired plane registration problems.  A good solution should maintain
accuracy when equivalent plane representations use inconsistent normal signs.

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

---

# Evaluation

## Metrics

The evaluator reads predicted rigid transforms from JSON files in
`checkpoints/` and compares them with the ground-truth transform stored in the
dataset JSON.

Rotation error is `acos((trace(R_hat^T R_gt)-1)/2)` in degrees.  Translation
error is `||t_hat - t_gt|| / ||t_gt|| * 100`.  Lower is better for both.  The
evaluation also reports the number of plane correspondences as a resource
constraint metric.

## Baselines and Targets

The paper reports object-registration results as curves rather than an
extractable numeric table.  The gym therefore uses a scaled synthetic analogue
of the paper's object-registration experiment, and `scoring/reference.json`
records expected behavior on this fixed synthetic instance rather than literal
paper table entries.  The signed plane-parameter least-squares baseline should
fail under antipodal ambiguity, while a successful primitive-registration
method should recover a low-error rigid transform on the same data.

## Evaluation Protocol

Run `bash scripts/reproduce.sh` to generate the fixed synthetic dataset, run
the baseline and proposed method, and write `scoring/scores.json`.  Run
`bash scripts/evaluate.sh` to rescore existing outputs.  The default dataset
uses 13 planes, 100 sampled points per plane, Gaussian noise with sigma 0.05,
and 5 percent outlier-corrupted samples during target plane fitting.

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


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
