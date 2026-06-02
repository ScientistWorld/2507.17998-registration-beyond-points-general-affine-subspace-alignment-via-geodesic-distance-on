# Evaluation Targets

## Primary: synthetic_plane_registration

Tests whether a solver can recover the rigid transform between paired noisy
planes in the object-registration setting.

- **Primary metric**: `translation_error_percent` (lower is better)
- **Secondary metric**: `rotation_error_deg` (lower is better)
- **Constraint metric**: `num_planes` (must not increase; using more primitives
  is resource scaling)
- **How to run**: `bash scripts/reproduce.sh` or `bash scripts/evaluate.sh`
