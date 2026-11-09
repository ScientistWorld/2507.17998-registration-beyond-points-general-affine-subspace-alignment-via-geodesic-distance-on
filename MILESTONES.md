# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim_plus`.
