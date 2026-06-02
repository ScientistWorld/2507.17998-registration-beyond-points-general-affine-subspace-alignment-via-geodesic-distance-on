# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Completed at `core_claim_plus`.  Higher milestones would require implementing the paper's BnB solver and additional RGB-D odometry / PnL / localization task families, which are beyond this compact plane-to-plane reproduction.
