# Train/Test Evaluation Design Notes

Current design (iteration 11, hardening; see `HARDENING.md` for the evidence).

- The method needs no training, so both evaluators *run* every solver
  registered in `scripts/solvers/<name>.sh` on a problems file that contains
  instance inputs only, then score the returned poses against ground truth
  that stays inside the evaluator process.
- Train (`eval/train/evaluate.py`) generates its instances with the public
  generator `data/synthetic_planes.py` from a visible seed.  Test
  (`eval/test/evaluate.py`) generates its instances with a frozen copy of the
  generator (`eval/test/hidden_instances.py`) from a seed that exists only in
  `eval/test/`.  The two evaluators share no code and use identical
  experiments, sizes (200 + 120 instances), metrics and validation.
- Validation: one pose per instance, finite, rotation in SO(3)
  (`||R^T R - I||_F <= 1e-6`, `det > 0`).  Any violation, crash or timeout fails
  the whole run at the metric caps (100% translation, 180 degrees rotation).
- Metrics are the paper's pose errors against ground truth (rotation geodesic
  angle, relative translation error capped at 100%), averaged per experiment.
- `scripts/evaluate_test.sh` takes no arguments; `--details <path>` is an
  optional diagnostic dump that does not change scores.

Superseded design (iterations 4-10): a single visible synthetic instance whose
plane indices were split into "train" and "test" halves, with prediction JSON
files under `checkpoints/`.  It exposed the ground truth, scored only one of
three weighted experiments through the no-argument entry point, and accepted
non-rigid or non-finite outputs; see `REDTEAM.md`.
