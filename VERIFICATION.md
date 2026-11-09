# Verification Report

> Predates the iteration-11 redesign of the evaluation (see `HARDENING.md`);
> the evaluator, data and score files described below were replaced.

## Initial Assessment

The workspace started at `core_claim_plus` with a working plane-to-plane
registration gym.  The paper method implementation is separated from the
evaluator, `scripts/reproduce.sh` regenerates the canonical scores, and
`python3 validate.py --compare` passes.  The claimed milestone is justified for
the scaled synthetic object-registration analogue: the implementation uses the
paper's affine Grassmannian plane-to-plane projection residual and is not a
surrogate model.

## Issues Found

- Minor: `briefing/evaluation.md` used method-specific wording (`proposed
  method`) in a method-agnostic file.
- Minor: `scoring/reference.json` used synthetic target values but did not
  carry explicit per-experiment notes explaining that they are not literal
  paper table values.
- Minor: generated scheduler logs under `jobs/` and raw trajectory logs were
  tracked even though they are ignored generated artifacts.
- Minor: the canonical `scripts/evaluate.sh --suite` path evaluated the
  built-in baseline and reproduced method artifacts instead of discovering all
  compatible method output files in a checkpoint directory.  The train/test
  evaluators already used method discovery, so this was a gym usability issue
  rather than evidence of fabricated scores.

## Fixes Applied

- Reworded `briefing/evaluation.md` to describe only the task, metrics, output
  format, and evaluation protocol.
- Added `notes` fields to each `reference.json` experiment documenting the
  scaled synthetic benchmark target values.
- Removed tracked `jobs/` and `trajectory/` generated artifacts, leaving the
  committed scores and documentation as the reproducibility record.
- Made the canonical suite evaluator method-discoverable.  It now reads all
  `*.json` prediction artifacts matching each experiment suffix under a
  checkpoint directory, deduplicates repeated method names, and scores whatever
  methods a future scientist produces through the same output interface.
- Updated `PROGRESS.md` and `MILESTONES.md` to reflect the final verification
  state.
- Submitted CPU verification job `e40e5cb7-0d5`; it completed with exit code 0
  and passed `python3 validate.py --compare`, including import separation,
  method-output evaluation, no committed `shared/` paths, train/test
  independence, train/test script rewiring, method-key consistency, and primary
  metric discrimination checks.

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
