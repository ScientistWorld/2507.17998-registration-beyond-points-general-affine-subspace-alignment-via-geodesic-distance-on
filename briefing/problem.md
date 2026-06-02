# Problem Definition

## Research Question

Estimate rigid 3D transformations between geometric primitives such as lines
and planes.  The benchmark asks whether a solver can recover rotation and
translation from paired affine features when the features are noisy and their
common vector parameterizations may have arbitrary signs.

## Why It Matters

Line and plane features summarize scene structure more compactly than raw
points and are useful in object registration, camera pose estimation, odometry,
and localization.  A reliable primitive registration solver should be robust to
noise, outliers, and representation choices that do not change the underlying
geometry.

## Success Criteria

Success is measured by low rotation and translation error against known ground
truth on paired plane registration problems.  A good solution should maintain
accuracy when equivalent plane representations use inconsistent normal signs.
