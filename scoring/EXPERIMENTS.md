# Experiment Overview

Both experiments are scored on held-out registration instances through the
hidden test; the visible train instances come from the same generator with a
different seed.  Each reports mean rotation error (degrees) and mean
translation error (percent of the true translation norm, capped at 100).

## object_registration

Tests whether a solver recovers an accurate rigid transform from 13 paired
planes when the observed planes are fitted from noisy point measurements
contaminated by 5 to 50 percent outlier points, and the observed planes'
vector descriptions have arbitrary signs.  This is the gym's analogue of the
paper's object-registration experiment.  It establishes accuracy under
measurement noise and representation ambiguity, in rotation and translation
jointly, so that a gain in one cannot hide a loss in the other.

## object_registration_mismatched

Same task, but 2, 3 or 4 of the 13 plane pairings are wrong.  Tests whether a
solver stays accurate when part of the given correspondences are outliers
rather than noisy inliers.  This is where accuracy on clean correspondences
does not carry over by itself, and it leaves room above the included reference
solver.
