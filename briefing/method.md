# Paper's Method

## Key Contribution

The paper derives an optimizable registration cost for affine subspaces by
embedding lines and planes into a higher-dimensional Grassmann manifold and
expressing zero geodesic distance through basis projection residuals.

## Approach

An affine primitive is represented by an orthonormal basis for its linear
subspace and by the unique displacement vector orthogonal to that subspace.
Under a rigid transform `(R, t)`, the basis rotates and the orthogonal
displacement is updated as `R b0 + R(I-AA^T)R^T t`.  The transformed primitive
is embedded as an orthonormal basis in one higher dimension.

The paper's Eq. 7 minimizes two coupled residual families: target direction
basis vectors are projected onto the rotated source linear subspace in the
original 3D space, and the target displacement basis is projected onto the
transformed source primitive embedded in one higher dimension.  For 3D
plane-to-plane registration, the rotation term can also be expressed with
plane normals and the translation term uses the embedded displacement basis.
The paper also proposes Branch-and-Bound inlier-set maximization for robust
global search and local LM refinement.

## Main Claims

The primary claim is that optimizing the affine Grassmannian basis-projection
cost improves line and plane registration, especially translation, because the
metric is invariant to sign ambiguity in vector parameters.  Secondary claims
include robust inlier-set maximization with Branch-and-Bound and successful
applications to RGB-D odometry, Perspective-n-Line, and correspondence-free
localization.
