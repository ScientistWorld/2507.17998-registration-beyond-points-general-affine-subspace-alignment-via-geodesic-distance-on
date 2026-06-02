# Research Direction

## Research Problem

This benchmark studies rigid registration from affine geometric primitives.
The central question is how to estimate accurate 3D transformations from line
or plane features when direct vector parameterizations are ambiguous or noisy.

## Core Contribution

The paper contributes geometry-aware costs and solvers for affine primitive
registration.  Improvements should address the same primitive-registration
problem: better objectives, search, robust estimation, or refinement for
line/plane subspaces under rigid motion.

## Approach Scope

Work should remain in the family of geometric registration methods operating
on affine features and rigid transforms.  Solver changes, alternative robust
estimators, different manifold parameterizations, better initialization, and
improved local optimization are in scope.

## Out of Bounds

Do not replace the problem with dense point-cloud registration, learned pose
regression from raw coordinates, or a method that uses additional data not
available to every solver.  Do not use ground-truth transforms, extra
correspondences, or denser measurements to bypass the primitive-registration
question.
