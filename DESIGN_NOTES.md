# Train/Test Evaluation Design Notes

## Checks performed

- Read `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh` side by side. The train wrapper calls `eval/train/evaluate.py` and writes `scoring/scores_train.json`; the test wrapper calls `eval/test/evaluate.py` and writes `scoring/scores_test.json`.
- Grepped the train/test evaluator code for cross-imports and hardcoded method defaults. The split evaluators discover prediction JSON files from `checkpoints/` and do not import from `method/`.
- Grepped `scoring/reference.json` and split evaluator code for paper-agreement metric names. No forbidden paper-fit metrics were found.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` are absent.
- Ran `bash -n` on both train/test wrapper scripts.

## Changes made

- Added `plane_offset_rmse` to both train and test evaluators. This scores the predicted rigid transform against the split-local plane geometry, adding a residual-based angle that a method overfit to the visible translation/rotation metrics must also satisfy on held-out planes.
- Changed split evaluator `num_planes` from the number of scored split indices to the full input plane count. This removes an artificial train/test difference where train emitted 7 and test emitted 6 for a method-independent resource-scale metric.
- Updated `scoring/reference.json` metric definitions with required descriptions, added `plane_offset_rmse`, and reduced `num_planes` to a small coefficient so it is context rather than a dominant score term.

## Runtime concerns for the next iteration

- The data files include `ground_truth`, and the existing prediction-artifact workflow scores already generated transforms. A future shortcut method could read visible ground truth while producing predictions; the current held-out split catches overfitting to visible plane indices but cannot fully defend against label leakage from the data files. A stronger runner-stage design would need hidden synthetic instances or a method invocation path that produces predictions on data without exposed ground truth.
- `plane_offset_rmse` was added statically but not exercised here, per this iteration's no-experiment rule. The runner iteration should confirm the metric is present in both `scores_train.json` and `scores_test.json` for `--suite` and does not saturate on the current reproduction.
- The test evaluator intentionally filters to methods present in `scoring/scores_train.json` when that file exists. The runner should verify this matches the intended final harness behavior when a future agent evaluates only a subset of methods.
