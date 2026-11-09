# Problem Definition

## Research Question

Estimate the rigid 3D transformation (rotation `R`, translation `t`) that maps
an object's model to its sensor observation, given paired *plane* features:
each exact model plane is paired with a plane fitted from noisy,
outlier-contaminated point measurements of the observed object.  Plane
features have no canonical vector parameterization (a plane and its antipodal
normal/offset describe the same geometry), the fitted planes carry measurement
error, and some plane correspondences may be wrong.

## Why It Matters

Line and plane features summarize scene structure more compactly than raw
points and are used in object registration, camera pose estimation, odometry,
and localization.  A primitive-registration solver has to be accurate under
noise, insensitive to arbitrary representation choices that do not change the
geometry, and robust when a fraction of the feature pairings is wrong.

## Success Criteria

Low rotation error (degrees) and low relative translation error (percent of the
true translation norm) against the ground truth, on registration instances the
solver has never seen, both when every plane pairing is correct and when a few
pairings are mismatched.  Outputs must be proper rigid transforms.
