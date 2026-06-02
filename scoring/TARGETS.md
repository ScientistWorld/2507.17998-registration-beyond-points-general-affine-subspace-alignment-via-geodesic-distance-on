# Evaluation Targets

## Primary: synthetic_plane_registration

Tests whether a solver can recover the rigid transform between paired noisy
planes in the object-registration setting.

- **Primary metric**: `translation_error_percent` (lower is better)
- **Secondary metric**: `rotation_error_deg` (lower is better)
- **Geometric consistency metric**: `plane_offset_rmse` (lower is better)
- **Fixed scale metadata**: `num_planes` (reported to show the 13-plane
  problem size; it is not a ranked score)
- **How to run**: `bash scripts/reproduce.sh` or `bash scripts/evaluate.sh --suite`

## Additional Settings

The suite also scores `synthetic_plane_registration_clean` and
`synthetic_plane_registration_outlier_0.10`.  These use the same data
generator, metrics, and 13-plane constraint while varying only the fitted-point
outlier ratio.

`scoring/scores.json` is the canonical full-instance score file.  The optional
`scores_train.json` and `scores_test.json` files use fixed plane-index splits
as supplemental diagnostics.
