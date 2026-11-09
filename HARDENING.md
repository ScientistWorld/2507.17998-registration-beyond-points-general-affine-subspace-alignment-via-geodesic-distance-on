# Hardening report (iteration 11)

DRAFT: results tables are filled in from `redteam/hardening/results/` after the
hardening job.

## What was wrong (from REDTEAM.md) and what changed

The old "hidden test" was a plane-index split of one visible synthetic
instance: its ground truth sat in `data/`, its translation was a constant in
the visible generator, the no-argument entry point scored only one of three
weighted experiments, its metrics were agreement with noisy observed normals
and a projected translation rather than the paper's pose errors, and any 3x3
matrix (non-rigid, NaN) was accepted.  These were not patchable one by one, so
the test was rebuilt:

| Problem | Fix |
|---|---|
| Test answers visible (`data/*.json` `ground_truth`), constant translation in the visible generator (seed replay) | Test instances are generated at test time inside `eval/test/` from a 128-bit seed that exists only there, with a frozen generator copy; every instance has its own random rotation (uniform on SO(3)) and translation.  Solvers receive inputs only; ground truth never leaves the evaluator process.  The old data files are deleted. |
| One fixed instance (no statistical power) | 200 + 120 test instances; every method sees the same instances (paired comparisons). |
| Data artifacts replaceable by the method | The test never reads `data/`; editing the public generator changes only train. |
| Only `synthetic_plane_registration` scored by the no-argument entry point | `bash scripts/evaluate_test.sh` (no arguments) scores every weighted experiment for every solver in `scripts/solvers/`. |
| Hidden metrics were not the paper's (noisy-normal agreement, projected translation, plane-offset residual) | Scored metrics are the paper's: rotation geodesic error (deg) and relative translation error (%) against ground truth; `plane_offset_rmse` and `num_planes` removed. |
| Non-rigid / NaN / Inf outputs accepted (NaN gave a false perfect rotation) | Every pose must be finite with `||R^T R - I||_F <= 1e-6` and `det R > 0`, and every instance must be answered; otherwise the whole run fails at the caps (100%, 180 deg) on every metric of every experiment. |
| Unbounded metrics | Translation error capped at 100% per instance (a zero-translation guess), rotation is bounded by 180 deg, so failures sit at the worst value and never outrank a solved run. |
| Method-written numbers | Only `rotation` and `translation` are read; every scored number is recomputed. |
| Experiments did not reach the paper's regime | Outlier ratios 5-50% with RANSAC plane fitting, as in the paper's Sec. 5.1, plus a mismatched-correspondence experiment where the paper's refinement falls short. |
