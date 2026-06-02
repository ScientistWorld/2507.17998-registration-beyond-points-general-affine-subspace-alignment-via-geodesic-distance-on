"""Synthetic plane registration data for the GrassmannRegistration gym.

The paper's Space Station mesh is not distributed with the paper.  This module
creates a small but non-trivial plane-to-plane registration problem with the
same ingredients used in Sec. 5.1: paired planes, noisy fitted measurements,
outlier-corrupted plane fitting, and a ground-truth rigid transform.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("zero vector")
    return v / n


def _plane_basis(normal: np.ndarray) -> np.ndarray:
    normal = _unit(normal)
    helper = np.array([1.0, 0.0, 0.0])
    if abs(float(helper @ normal)) > 0.85:
        helper = np.array([0.0, 1.0, 0.0])
    u = _unit(np.cross(normal, helper))
    v = _unit(np.cross(normal, u))
    return np.column_stack([u, v])


def _random_rotation(rng: np.random.Generator) -> np.ndarray:
    axis = _unit(rng.normal(size=3))
    angle = rng.uniform(-1.0, 1.0)
    k = np.array(
        [[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]]
    )
    return np.eye(3) + np.sin(angle) * k + (1.0 - np.cos(angle)) * (k @ k)


def _fit_plane(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    centroid = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - centroid, full_matrices=False)
    normal = _unit(vh[-1])
    offset = float(normal @ centroid)
    if offset < 0.0:
        normal = -normal
        offset = -offset
    basis = _plane_basis(normal)
    displacement = offset * normal
    return basis, displacement, offset


def _sample_plane_points(
    rng: np.random.Generator,
    normal: np.ndarray,
    displacement: np.ndarray,
    count: int,
    extent: float,
    noise: float,
    outlier_ratio: float,
) -> np.ndarray:
    basis = _plane_basis(normal)
    coeff = rng.uniform(-extent, extent, size=(count, 2))
    points = displacement + coeff @ basis.T
    points += rng.normal(scale=noise, size=points.shape)
    n_out = int(round(count * outlier_ratio))
    if n_out:
        idx = rng.choice(count, n_out, replace=False)
        points[idx] = rng.uniform(-2.0 * extent, 2.0 * extent, size=(n_out, 3))
    return points


def generate_dataset(
    output: Path,
    seed: int = 7,
    n_planes: int = 13,
    points_per_plane: int = 100,
    noise: float = 0.05,
    outlier_ratio: float = 0.2,
) -> None:
    rng = np.random.default_rng(seed)
    source = []
    target = []
    raw_plane_parameters = []

    # Avoid degenerate normal sets by mixing axis-aligned and oblique planes.
    base_normals = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 1],
        [1, -1, 0],
        [1, 0, -1],
        [0, 1, -1],
        [1, 1, 1],
        [1, -1, 1],
        [-1, 1, 1],
        [2, 1, -1],
    ]
    normals = [_unit(np.asarray(base_normals[i % len(base_normals)], dtype=float)) for i in range(n_planes)]
    offsets = rng.uniform(0.8, 3.5, size=n_planes)

    r_gt = _random_rotation(rng)
    t_gt = np.array([0.85, -0.55, 1.15])

    for i, (n_s, h_s) in enumerate(zip(normals, offsets)):
        c_s = h_s * n_s
        b_s = _plane_basis(n_s)
        source.append({"basis": b_s.tolist(), "displacement": c_s.tolist(), "normal": n_s.tolist()})

        n_t_true = r_gt @ n_s
        c_t_true = r_gt @ c_s + (np.eye(3) - np.outer(n_t_true, n_t_true)) @ t_gt
        pts = _sample_plane_points(rng, n_t_true, c_t_true, points_per_plane, 2.5, noise, outlier_ratio)
        b_t, c_t, h_t = _fit_plane(pts)
        n_t = _unit(np.cross(b_t[:, 0], b_t[:, 1]))
        if n_t @ c_t < 0.0:
            n_t = -n_t
            b_t[:, 1] = -b_t[:, 1]
        target.append({"basis": b_t.tolist(), "displacement": c_t.tolist(), "normal": n_t.tolist()})

        # Parameter baselines must choose one antipodal plane representation.
        # Deliberately make the signs inconsistent to reproduce the ambiguity
        # described in Fig. 1 and Sec. 5.1.
        sign = -1.0 if i % 2 else 1.0
        raw_plane_parameters.append({"normal": (sign * n_t).tolist(), "offset": float(sign * h_t)})

    payload = {
        "metadata": {
            "seed": seed,
            "n_planes": n_planes,
            "points_per_plane": points_per_plane,
            "noise": noise,
            "outlier_ratio": outlier_ratio,
            "deviation": "Synthetic substitute for the unavailable Space Station model.",
        },
        "ground_truth": {"rotation": r_gt.tolist(), "translation": t_gt.tolist()},
        "source": source,
        "target": target,
        "target_signed_parameters": raw_plane_parameters,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--outlier-ratio", type=float, default=0.2)
    parser.add_argument("--noise", type=float, default=0.05)
    args = parser.parse_args()
    generate_dataset(args.output, seed=args.seed, outlier_ratio=args.outlier_ratio, noise=args.noise)


if __name__ == "__main__":
    main()
