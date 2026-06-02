"""Plane-parameter least-squares baseline.

This intentionally follows the baseline family criticized in the paper:
planes are represented as signed Euclidean parameters, so antipodal choices of
the same geometric plane can corrupt the translation estimate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def _kabsch(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    h = a.T @ b
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1.0
        r = vt.T @ u.T
    return r


def run(input_path: Path, output_path: Path) -> None:
    data = json.loads(input_path.read_text())
    normals_s = np.asarray([s["normal"] for s in data["source"]], dtype=float)
    signed_t = data["target_signed_parameters"]
    normals_t = np.asarray([p["normal"] for p in signed_t], dtype=float)
    offsets_s = np.asarray([np.linalg.norm(s["displacement"]) for s in data["source"]], dtype=float)
    offsets_t = np.asarray([p["offset"] for p in signed_t], dtype=float)

    r = _kabsch(normals_s, normals_t)
    rows = normals_t
    vals = offsets_t - np.einsum("ij,ij->i", normals_t, (r @ (normals_s * offsets_s[:, None]).T).T)
    t = np.linalg.lstsq(rows, vals, rcond=None)[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "method": "plane_parameter_lstsq",
                "rotation": r.tolist(),
                "translation": t.tolist(),
                "rotvec": Rotation.from_matrix(r).as_rotvec().tolist(),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--output", type=Path, default=Path("checkpoints/plane_parameter_lstsq.json"))
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
