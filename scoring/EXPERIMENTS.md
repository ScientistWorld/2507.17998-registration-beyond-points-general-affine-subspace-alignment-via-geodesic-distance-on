# Experiment Overview

## synthetic_plane_registration

Tests whether a geometric registration system can estimate an accurate rigid
transform from paired planes when the measurements are noisy and equivalent
plane representations may be signed inconsistently.  The experiment captures
the central object-registration question from the paper at a scale that is
small enough to run quickly in this reusable environment.

## synthetic_plane_registration_clean

Checks the same registration task when plane measurements have Gaussian noise
but no fitted-point outliers.  This verifies that a method handles the
representation ambiguity without relying on outlier difficulty.

## synthetic_plane_registration_outlier_0.10

Repeats the same registration task with a higher fitted-point outlier ratio.
This probes whether the recovered transform remains useful when the target
plane estimates are more corrupted.
