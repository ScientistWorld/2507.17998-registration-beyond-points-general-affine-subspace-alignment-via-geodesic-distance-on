# Verification Report

## Initial Assessment

The workspace started at `core_claim_plus` with a working plane-to-plane
registration gym.  The paper method implementation is separated from the
evaluator, `scripts/reproduce.sh` regenerates the canonical scores, and
`python3 validate.py --compare` passes.  The claimed milestone is justified for
the scaled synthetic object-registration analogue.

## Issues Found

- Minor: `briefing/evaluation.md` used method-specific wording (`proposed
  method`) in a method-agnostic file.
- Minor: `scoring/reference.json` used synthetic target values but did not
  carry explicit per-experiment notes explaining that they are not literal
  paper table values.
- Minor: generated scheduler logs under `jobs/` and raw trajectory logs were
  tracked even though they are ignored generated artifacts.

## Fixes Applied

- Reworded `briefing/evaluation.md` to describe only the task, metrics, output
  format, and evaluation protocol.
- Added `notes` fields to each `reference.json` experiment documenting the
  scaled synthetic benchmark target values.
- Removed tracked `jobs/` and `trajectory/` generated artifacts, leaving the
  committed scores and documentation as the reproducibility record.
- Updated `PROGRESS.md` and `MILESTONES.md` to reflect the final verification
  state.

## Final Judgment

The workspace is ready to serve as a research gym in both improve and
from-scratch modes.  The main caveat is that the original CAD benchmark is not
available, so the gym uses a documented synthetic 13-plane substitute; within
that scope, the evaluation is reusable and discriminates the included baseline
from the reproduced method.

- Milestone: core_claim_plus
- Ready for gym use: yes
- Confidence: medium
- Key limitation: synthetic substitute data only
