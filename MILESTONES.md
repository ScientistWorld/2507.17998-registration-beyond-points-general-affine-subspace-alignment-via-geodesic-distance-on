# Reproduction Milestones

**Current: core_claim**

<!-- Milestone levels (update "Current" above as you progress):
  none             — just started, no meaningful progress yet
  method_runs      — the paper's method executes end-to-end without errors
  core_claim       — minimum experiment supports the paper's central claim
  core_claim_plus  — core claim reproduced on additional settings
  secondary_claims — secondary results or contributions reproduced
  majority         — more than half of reported results reproduced
  near_complete    — most results reproduced, only minor gaps remain
  full             — all reported results reproduced
-->

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim`.
