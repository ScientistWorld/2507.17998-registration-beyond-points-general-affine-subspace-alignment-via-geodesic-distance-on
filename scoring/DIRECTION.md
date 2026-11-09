# Research Direction

## Research Problem

This benchmark studies rigid registration from affine geometric primitives
(here, planes).  The central question is how to estimate accurate 3D
transformations from plane features when their vector parameterizations are
sign-ambiguous, the fitted features are noisy, and some feature pairings are
wrong.

## Core Contribution

The paper contributes geometry-aware registration costs for affine primitives
and robust solvers built on them.  Improvements should address the same
primitive-registration problem: better objectives or noise weighting,
outlier-robust or globally optimal search over correspondences, better
initialization, and better local refinement for line/plane subspaces under
rigid motion.

## Approach Scope

In scope: alternative costs on the plane features, robust estimators and
inlier-set maximization over correspondences, consensus or branch-and-bound
search, uncertainty weighting, manifold parameterizations, and refinement
strategies, all operating on the given paired planes and returning a rigid
transform.

## Out of Bounds

Do not use ground truth, the evaluators' seeds or code, or any information
not present in a solver's `problems.json`.  Do not replace the problem with
dense point-cloud registration or learned pose regression from generator
internals, and do not change the instance distribution, the number of planes
or the experiment sizes.  Outputs must be proper rigid transforms for every
instance.
