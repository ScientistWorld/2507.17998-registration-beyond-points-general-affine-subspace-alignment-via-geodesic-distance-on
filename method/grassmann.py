"""Affine Grassmannian plane-to-plane registration.

This implements the paper's optimizable basis-projection residual for
Graff(2, 3) plane registration.  The transformed source plane is embedded in
Gr(3, 4) using Eq. (5), and each residual projects the target embedded basis
onto that transformed source basis as in Eq. (7) / Corollary 2.3.
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("zero vector")
    return v / n


def _rotvec_to_matrix(rotvec: np.ndarray) -> np.ndarray:
    return Rotation.from_rotvec(rotvec).as_matrix()


def _matrix_to_rotvec(matrix: np.ndarray) -> np.ndarray:
    return Rotation.from_matrix(matrix).as_rotvec()


def _tilde(v: np.ndarray) -> np.ndarray:
    out = np.r_[v, 1.0]
    return out / np.linalg.norm(out)


def _kabsch(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    h = a.T @ b
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1.0
        r = vt.T @ u.T
    return r


def _rotation_initial(normals_s: np.ndarray, normals_t: np.ndarray) -> np.ndarray:
    """Sign-invariant normal alignment by exhaustive antipodal assignments."""
    best_r = np.eye(3)
    best_cost = np.inf
    n = len(normals_s)
    # 13 planes gives 8192 assignments, cheap and deterministic at this scale.
    for signs in product([-1.0, 1.0], repeat=n):
        signed = normals_t * np.asarray(signs)[:, None]
        r = _kabsch(normals_s, signed)
        dots = np.clip(np.abs(np.sum((normals_s @ r.T) * normals_t, axis=1)), 0.0, 1.0)
        cost = float(np.sum(np.arccos(dots) ** 2))
        if cost < best_cost:
            best_cost = cost
            best_r = r
    return best_r


def _embedded_source_basis(basis_s: np.ndarray, disp_s: np.ndarray, r: np.ndarray, t: np.ndarray) -> np.ndarray:
    normal_s = _unit(np.cross(basis_s[:, 0], basis_s[:, 1]))
    projector_perp = np.outer(normal_s, normal_s)
    disp_prime = r @ disp_s + r @ projector_perp @ r.T @ t
    y = np.zeros((4, 3))
    y[:3, :2] = r @ basis_s
    y[:, 2] = _tilde(disp_prime)
    return y


def residual_vector(params: np.ndarray, source: list[dict], target: list[dict]) -> np.ndarray:
    r = _rotvec_to_matrix(params[:3])
    t = params[3:6]
    residuals: list[np.ndarray] = []
    for src, dst in zip(source, target):
        b_s = np.asarray(src["basis"], dtype=float)
        c_s = np.asarray(src["displacement"], dtype=float)
        b_t = np.asarray(dst["basis"], dtype=float)
        c_t = np.asarray(dst["displacement"], dtype=float)
        y = _embedded_source_basis(b_s, c_s, r, t)
        p = y @ y.T
        # Eq. (7): both target plane basis vectors plus target displacement
        # basis must be spanned by the transformed embedded source plane.
        for j in range(2):
            a_bar = np.r_[b_t[:, j], 0.0]
            residuals.append(p @ a_bar - a_bar)
        c_tilde = _tilde(c_t)
        residuals.append(p @ c_tilde - c_tilde)
    return np.concatenate(residuals)


def fit_translation_linear(source: list[dict], target: list[dict], r: np.ndarray) -> np.ndarray:
    rows = []
    vals = []
    for src, dst in zip(source, target):
        n_s = _unit(np.cross(np.asarray(src["basis"])[:, 0], np.asarray(src["basis"])[:, 1]))
        n_t = _unit(np.cross(np.asarray(dst["basis"])[:, 0], np.asarray(dst["basis"])[:, 1]))
        c_s = np.asarray(src["displacement"], dtype=float)
        c_t = np.asarray(dst["displacement"], dtype=float)
        n_rs = r @ n_s
        sign = 1.0 if n_rs @ n_t >= 0.0 else -1.0
        rows.append(sign * n_t)
        vals.append(float(sign * n_t @ c_t - n_rs @ (r @ c_s)))
    return np.linalg.lstsq(np.vstack(rows), np.asarray(vals), rcond=None)[0]


def run(input_path: Path, output_path: Path) -> None:
    data = json.loads(input_path.read_text())
    source = data["source"]
    target = data["target"]
    normals_s = np.asarray([s["normal"] for s in source], dtype=float)
    normals_t = np.asarray([t["normal"] for t in target], dtype=float)
    r0 = _rotation_initial(normals_s, normals_t)
    t0 = fit_translation_linear(source, target, r0)
    x0 = np.r_[_matrix_to_rotvec(r0), t0]
    result = least_squares(
        residual_vector,
        x0,
        args=(source, target),
        loss="soft_l1",
        f_scale=0.05,
        max_nfev=500,
        xtol=1e-10,
        ftol=1e-10,
        gtol=1e-10,
    )
    r = _rotvec_to_matrix(result.x[:3])
    payload = {
        "method": "grassmann_refine",
        "rotation": r.tolist(),
        "translation": result.x[3:6].tolist(),
        "cost": float(np.sum(residual_vector(result.x, source, target) ** 2)),
        "nfev": int(result.nfev),
        "success": bool(result.success),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--output", type=Path, default=Path("checkpoints/grassmann_refine.json"))
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
