# Evaluation Targets

Both experiments are scored on the hidden test (`bash scripts/evaluate_test.sh`,
no arguments) and, on visible instances, by `bash scripts/evaluate.sh` and
`bash scripts/evaluate_train.sh`.  Every metric is a mean over instances; lower
is better.

## object_registration (weight 0.6)

Recover the rigid transform from 13 paired noisy planes, 5-50% outlier points.

- **Primary metric**: `translation_error_percent` (coefficient 1.0) — the
  paper's headline object-registration quantity.
- **Constraint metric**: `rotation_error_deg` (coefficient 1.0) — the quantity
  the paper's refinement trades away; scored at equal weight so a translation
  gain cannot be bought with rotation accuracy.
- Reference vs baseline: the reference must stay far below the signed
  plane-parameter baseline in translation error while not losing rotation
  accuracy against it.

## object_registration_mismatched (weight 0.4)

Same task with 2-4 of the 13 plane pairings mismatched.

- **Primary metric**: `translation_error_percent` (coefficient 1.0).
- **Constraint metric**: `rotation_error_deg` (coefficient 1.0).
- Purpose: robustness to outlier correspondences; this is where the reference
  falls short and a better method can score higher.

## Validity constraint (both experiments)

Every instance must receive a finite proper rotation in SO(3) and a finite
translation; otherwise the run scores 100% / 180 degrees on every metric of
both experiments.

Reference and baseline values are in `scoring/reference.json`; the reproduced
values are in `scoring/scores_test.json` (hidden test), `scoring/scores_train.json`
and `scoring/scores.json` (visible instances).
