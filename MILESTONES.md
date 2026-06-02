# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim_plus`.
