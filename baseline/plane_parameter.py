"""Plane-parameter least-squares baseline.

This intentionally follows the baseline family criticized in the paper:
planes are represented as signed Euclidean parameters, so antipodal choices of
the same geometric plane can corrupt the translation estimate.  Rotation is
estimated with sign-invariant normal alignment so the comparison isolates the
translation weakness emphasized in the paper's object-registration discussion.
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np


def _kabsch(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    h = a.T @ b
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1.0
        r = vt.T @ u.T
    return r


def _rotation_initial(normals_s: np.ndarray, normals_t: np.ndarray) -> np.ndarray:
    best_r = np.eye(3)
    best_cost = np.inf
    n = len(normals_s)
    for signs in product([-1.0, 1.0], repeat=n):
        signed = normals_t * np.asarray(signs)[:, None]
        r = _kabsch(normals_s, signed)
        dots = np.clip(np.abs(np.sum((normals_s @ r.T) * normals_t, axis=1)), 0.0, 1.0)
        cost = float(np.sum(np.arccos(dots) ** 2))
        if cost < best_cost:
            best_cost = cost
            best_r = r
    return best_r


def estimate(instance: dict) -> tuple[np.ndarray, np.ndarray]:
    """Signed plane-parameter registration of one instance."""
    normals_s = np.asarray([s["normal"] for s in instance["source"]], dtype=float)
    signed_t = instance["target_signed_parameters"]
    normals_t = np.asarray([p["normal"] for p in signed_t], dtype=float)
    offsets_s = np.asarray([np.linalg.norm(s["displacement"]) for s in instance["source"]], dtype=float)
    offsets_t = np.asarray([p["offset"] for p in signed_t], dtype=float)

    r = _rotation_initial(normals_s, normals_t)
    rotated_normals = (r @ normals_s.T).T
    # Signed Euclidean plane parameters compare the transformed source offset
    # against the selected target offset.  If an equivalent target plane is
    # represented by the antipodal parameter, this least-squares system asks
    # translation to satisfy an incompatible offset equation.
    t = np.linalg.lstsq(rotated_normals, offsets_t - offsets_s, rcond=None)[0]
    return r, t


def run(problems_path: Path, predictions_path: Path) -> None:
    """Solver contract: read a problems file, write one pose per instance id."""
    instances = json.loads(problems_path.read_text())["instances"]
    predictions = {}
    for instance in instances:
        r, t = estimate(instance)
        predictions[instance["id"]] = {"rotation": r.tolist(), "translation": t.tolist()}
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.write_text(json.dumps({"method": "plane_parameter_lstsq", "predictions": predictions}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Signed plane-parameter least-squares baseline solver.")
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    run(args.problems, args.predictions)


if __name__ == "__main__":
    main()
