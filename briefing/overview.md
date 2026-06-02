# Overview

- **Paper ID:** 2507.17998
- **Title:** Registration beyond Points: General Affine Subspace Alignment via Geodesic Distance on Grassmann Manifold
- **Domain:** Computer Vision / Geometric Registration
- **TL;DR:** The paper turns affine Grassmannian distances between lines and planes into an explicit rigid-transform objective for registration.

## Short Summary

The paper studies rigid registration from higher-order primitives such as 3D
lines and planes.  Its core contribution is an explicit affine Grassmannian
cost in terms of rotation and translation, avoiding the sign ambiguity of
common vector parameterizations.  The authors apply this cost directly and
inside Branch-and-Bound solvers for plane registration, RGB-D odometry,
Perspective-n-Line, and localization.

## Key Results

- On Replica RGB-D odometry, the proposed Refine and BnB variants report the
  best or near-best APE across Office and Room sequences.
- On real chessboard PnL, BnB reports 0.25 degree rotation error and Refine
  reports 1.13 mm translation error.
- The text reports robustness on synthetic PnL up to 80 percent outliers.
