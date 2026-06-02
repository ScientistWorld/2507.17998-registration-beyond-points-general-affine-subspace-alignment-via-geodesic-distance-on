# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-02 17:27] - core_claim_plus
- Implemented and scored the paper's affine Grassmannian plane-to-plane projection residual on a fixed synthetic object-registration analogue.
- Added three settings with 0%, 5%, and 10% fitted-point outlier ratios; the Grassmann method substantially improves rotation and translation error over the signed plane-parameter baseline in all three.
- Packaged reusable data generation, method, baseline, and evaluator scripts; `scripts/reproduce.sh` runs the full suite and writes `scoring/scores.json`.

## Stop Justification
- Not stopped yet; submitting a CPU reproducibility job to verify the packaged suite after the continuation audit.
