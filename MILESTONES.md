# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

### [2026-06-02 18:00] - core_claim_plus
- Ran the actual affine Grassmannian plane-to-plane residual on three synthetic object-registration settings: 0%, 5%, and 10% fitted-point outliers.
- The proposed method substantially reduced translation and rotation error relative to the signed plane-parameter baseline on all settings.
- Validation passed with `python validate.py --compare`.

### [2026-06-02 18:20] - core_claim_plus
- Audited the implementation and confirmed it implements the paper's affine Grassmannian embedded basis-projection residual for plane-to-plane registration, not a surrogate.
- Fixed script interpreter selection so standalone evaluation and reproduction use the same dependency-installed Python interpreter.
- Reran `bash scripts/reproduce.sh && python3 validate.py --compare` successfully.

## Stop Justification
- Completed a trustworthy `core_claim_plus` reproduction on the scaled synthetic plane-registration suite. Higher milestones would require implementing additional task families such as line-to-plane PnL or the full BnB solver.
