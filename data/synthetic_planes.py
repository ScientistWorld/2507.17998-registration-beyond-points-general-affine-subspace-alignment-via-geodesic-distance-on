"""Synthetic plane-to-plane registration problems for this gym.

Scaled analogue of the paper's object-registration experiment (Sec. 5.1):

* a 13-plane object in its model frame (the *source* planes, exact);
* a random rigid transform (uniform rotation, translation of norm 1.5-3);
* 100 point measurements per plane in the sensor frame with Gaussian noise
  (sigma 0.05), of which a given fraction are outliers drawn uniformly from a
  cube of side 20 around the transformed object;
* each *target* plane fitted from its own measurements by RANSAC followed by a
  least-squares refit on the inliers (the paper fits planes from the raw
  measurements and identifies inliers);
* optionally, a few plane correspondences are mismatched: the targets of
  ``n_mismatched`` randomly chosen planes are cyclically permuted.

What a solver sees for one instance (no ground truth):

``source``  list of model planes ``{basis (3x2), displacement (3,), normal (3,)}``
``target``  list of fitted planes in the sensor frame with the same fields.
            ``displacement`` is the foot of the perpendicular from the origin;
            the normal sign follows the convention ``normal . displacement >= 0``.
``target_signed_parameters``  the same fitted target planes as
            ``{normal, offset}`` with an arbitrary sign chosen per plane.

The ground truth ``{rotation R, translation t}`` maps source to target
coordinates: ``x_target = R x_source + t``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

N_PLANES = 13
POINTS_PER_PLANE = 100
NOISE_SIGMA = 0.05
PATCH_HALF_EXTENT = 1.0
OFFSET_RANGE = (0.8, 3.5)
TRANSLATION_NORM_RANGE = (1.5, 3.0)
OUTLIER_CUBE_SIDE = 20.0
RANSAC_ITERATIONS = 200
RANSAC_THRESHOLD = 3.0 * NOISE_SIGMA

# Mixed axis-aligned and oblique model normals (no two are parallel).
_BASE_NORMALS = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 1),
    (1, -1, 0),
    (1, 0, -1),
    (0, 1, -1),
    (1, 1, 1),
    (1, -1, 1),
    (-1, 1, 1),
    (2, 1, -1),
)
NORMALS = np.array([np.asarray(n, dtype=float) / np.linalg.norm(n) for n in _BASE_NORMALS])


def make_rng(entropy: int, *key: int) -> np.random.Generator:
    """Independent PCG64 stream for (entropy, key)."""
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy, spawn_key=tuple(key))))


def plane_basis(normal: np.ndarray) -> np.ndarray:
    """Orthonormal 3x2 basis (u, v) of the plane with u x v = normal."""
    normal = normal / np.linalg.norm(normal)
    helper = np.array([1.0, 0.0, 0.0])
    if abs(float(helper @ normal)) > 0.85:
        helper = np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    v = np.cross(normal, u)
    v /= np.linalg.norm(v)
    return np.column_stack([u, v])


def random_rotation(rng: np.random.Generator) -> np.ndarray:
    """Uniformly distributed rotation from a random unit quaternion."""
    q = rng.normal(size=4)
    w, x, y, z = q / np.linalg.norm(q)
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ]
    )


def random_translation(rng: np.random.Generator) -> np.ndarray:
    direction = rng.normal(size=3)
    direction /= np.linalg.norm(direction)
    return direction * rng.uniform(*TRANSLATION_NORM_RANGE)


def _lsq_plane(points: np.ndarray) -> tuple[np.ndarray, float]:
    centroid = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - centroid, full_matrices=False)
    normal = vh[-1] / np.linalg.norm(vh[-1])
    return normal, float(normal @ centroid)


def fit_plane_ransac(rng: np.random.Generator, points: np.ndarray) -> tuple[np.ndarray, float]:
    """RANSAC plane hypothesis, then least-squares refits on the inlier set.

    Returns a unit normal and offset >= 0 with ``normal . x = offset``.
    """
    count = len(points)
    picks = rng.integers(0, count, size=(RANSAC_ITERATIONS, 3))
    a, b, c = points[picks[:, 0]], points[picks[:, 1]], points[picks[:, 2]]
    normals = np.cross(b - a, c - a)
    norms = np.linalg.norm(normals, axis=1)
    valid = norms > 1e-12
    normals = normals / np.where(valid, norms, 1.0)[:, None]
    offsets = np.einsum("kj,kj->k", normals, a)
    residuals = np.abs(points @ normals.T - offsets[None, :])
    support = (residuals < RANSAC_THRESHOLD).sum(axis=0)
    support[~valid] = -1
    best = int(np.argmax(support))
    normal, offset = _lsq_plane(points[residuals[:, best] < RANSAC_THRESHOLD])
    for _ in range(2):
        inliers = np.abs(points @ normal - offset) < RANSAC_THRESHOLD
        if int(inliers.sum()) < 3:
            break
        normal, offset = _lsq_plane(points[inliers])
    if offset < 0.0:
        normal, offset = -normal, -offset
    return normal, offset


def _measure_plane(
    rng: np.random.Generator,
    basis_s: np.ndarray,
    displacement_s: np.ndarray,
    rotation: np.ndarray,
    translation: np.ndarray,
    outlier_ratio: float,
) -> np.ndarray:
    coeff = rng.uniform(-PATCH_HALF_EXTENT, PATCH_HALF_EXTENT, size=(POINTS_PER_PLANE, 2))
    model_points = displacement_s + coeff @ basis_s.T
    points = model_points @ rotation.T + translation
    points = points + rng.normal(scale=NOISE_SIGMA, size=points.shape)
    n_out = int(round(POINTS_PER_PLANE * outlier_ratio))
    if n_out:
        chosen = rng.permutation(POINTS_PER_PLANE)[:n_out]
        half = 0.5 * OUTLIER_CUBE_SIDE
        points[chosen] = translation + rng.uniform(-half, half, size=(n_out, 3))
    return points


def _plane_record(basis: np.ndarray, displacement: np.ndarray, normal: np.ndarray) -> dict:
    return {"basis": basis.tolist(), "displacement": displacement.tolist(), "normal": normal.tolist()}


def generate_instance(
    rng: np.random.Generator, outlier_ratio: float, n_mismatched: int = 0
) -> tuple[dict, dict]:
    """Return ``(problem, truth)`` for one registration instance."""
    if not 0.0 <= outlier_ratio < 1.0:
        raise ValueError("outlier_ratio must be in [0, 1)")
    if n_mismatched == 1 or not 0 <= n_mismatched <= N_PLANES - 3:
        raise ValueError("n_mismatched must be 0 or in [2, N_PLANES - 3]")
    offsets = rng.uniform(*OFFSET_RANGE, size=N_PLANES)
    rotation = random_rotation(rng)
    translation = random_translation(rng)

    source, target, signed = [], [], []
    for i in range(N_PLANES):
        normal_s = NORMALS[i]
        basis_s = plane_basis(normal_s)
        displacement_s = offsets[i] * normal_s
        source.append(_plane_record(basis_s, displacement_s, normal_s))

        points = _measure_plane(rng, basis_s, displacement_s, rotation, translation, outlier_ratio)
        normal_t, offset_t = fit_plane_ransac(rng, points)
        target.append(_plane_record(plane_basis(normal_t), offset_t * normal_t, normal_t))
        sign = -1.0 if rng.random() < 0.5 else 1.0
        signed.append({"normal": (sign * normal_t).tolist(), "offset": float(sign * offset_t)})

    if n_mismatched:
        chosen = rng.permutation(N_PLANES)[:n_mismatched]
        donors = np.roll(chosen, 1)
        fitted_target, fitted_signed = list(target), list(signed)
        for dst, src in zip(chosen, donors):
            target[int(dst)] = fitted_target[int(src)]
            signed[int(dst)] = fitted_signed[int(src)]

    problem = {"source": source, "target": target, "target_signed_parameters": signed}
    truth = {"rotation": rotation.tolist(), "translation": translation.tolist()}
    return problem, truth


def generate_suite(entropy: int, experiments) -> tuple[list[dict], dict, dict]:
    """Generate every instance of the given experiment specs.

    ``experiments`` is a sequence of dicts with keys ``name``, ``count``,
    ``outlier_ratios`` and ``mismatched``.  Instances are shuffled across
    experiments and given opaque ids.  Returns ``(problems, truths,
    membership)``; ``problems`` carry only solver inputs.
    """
    records = []
    for e_idx, spec in enumerate(experiments):
        ratios = tuple(spec["outlier_ratios"])
        mismatched = tuple(spec["mismatched"])
        for j in range(int(spec["count"])):
            ratio = ratios[j % len(ratios)]
            k = mismatched[(j // len(ratios)) % len(mismatched)]
            problem, truth = generate_instance(make_rng(entropy, e_idx, j), ratio, k)
            records.append((spec["name"], problem, truth, ratio, k))
    order = make_rng(entropy, len(experiments)).permutation(len(records))
    problems, truths, membership = [], {}, {}
    for new_idx, old_idx in enumerate(order):
        name, problem, truth, ratio, k = records[int(old_idx)]
        instance_id = f"inst-{new_idx:04d}"
        problems.append({"id": instance_id, **problem})
        truths[instance_id] = truth
        membership[instance_id] = {"experiment": name, "outlier_ratio": ratio, "mismatched": k}
    return problems, truths, membership


def main() -> None:
    parser = argparse.ArgumentParser(description="Write example plane-registration problems for development.")
    parser.add_argument("--entropy", type=int, default=12345)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--outlier-ratio", type=float, default=0.2)
    parser.add_argument("--mismatched", type=int, default=0)
    parser.add_argument("--problems", type=Path, default=Path("tmp/example_problems.json"))
    parser.add_argument("--truths", type=Path, default=Path("tmp/example_truths.json"))
    args = parser.parse_args()
    spec = {
        "name": "example",
        "count": args.count,
        "outlier_ratios": (args.outlier_ratio,),
        "mismatched": (args.mismatched,),
    }
    problems, truths, _ = generate_suite(args.entropy, [spec])
    args.problems.parent.mkdir(parents=True, exist_ok=True)
    args.truths.parent.mkdir(parents=True, exist_ok=True)
    args.problems.write_text(json.dumps({"format": "plane-registration-problems/v1", "instances": problems}))
    args.truths.write_text(json.dumps(truths, indent=1))


if __name__ == "__main__":
    main()
