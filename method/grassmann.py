"""Affine Grassmannian plane-to-plane registration.

This implements the paper's optimizable basis-projection residual for
Graff(2, 3) plane registration.  Eq. (7) separates the 3D linear-subspace
alignment term from the 4D embedded affine-displacement term: target plane
basis vectors are projected onto the rotated source plane basis in R^3, while
the target displacement basis is projected onto the embedded transformed
source plane in Gr(3, 4).
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
        rotated_basis = r @ b_s
        p_linear = rotated_basis @ rotated_basis.T
        y = _embedded_source_basis(b_s, c_s, r, t)
        p_affine = y @ y.T
        # Eq. (7): direction bases use the 3D projector P_{R·B}; only the
        # displacement term uses the embedded affine Grassmannian projector.
        for j in range(2):
            a = b_t[:, j]
            residuals.append(p_linear @ a - a)
        c_tilde = _tilde(c_t)
        residuals.append(p_affine @ c_tilde - c_tilde)
    return np.concatenate(residuals)


def fit_translation_linear(source: list[dict], target: list[dict], r: np.ndarray) -> np.ndarray:
    """Closed-form affine displacement initializer from Theorem 1.

    For a transformed source plane, c' = R c + (R n n^T R^T) t.  Projecting
    both sides onto the transformed normal gives one linear equation in t per
    plane.  This uses the sign-invariant displacement vector, not arbitrary
    signed plane parameters.
    """
    rows = []
    vals = []
    for src, dst in zip(source, target):
        n_s = _unit(np.cross(np.asarray(src["basis"])[:, 0], np.asarray(src["basis"])[:, 1]))
        c_s = np.asarray(src["displacement"], dtype=float)
        c_t = np.asarray(dst["displacement"], dtype=float)
        n_rs = r @ n_s
        rows.append(n_rs)
        vals.append(float(n_rs @ (c_t - r @ c_s)))
    return np.linalg.lstsq(np.vstack(rows), np.asarray(vals), rcond=None)[0]


def _solve_with_fixed_rotation(
    r: np.ndarray,
    t0: np.ndarray,
    source: list[dict],
    target: list[dict],
    loss: str = "soft_l1",
    f_scale: float = 0.05,
) -> tuple[np.ndarray, float, int, bool]:
    rotvec = _matrix_to_rotvec(r)

    def residual_t(t: np.ndarray) -> np.ndarray:
        return residual_vector(np.r_[rotvec, t], source, target)

    result = least_squares(
        residual_t,
        t0,
        loss=loss,
        f_scale=f_scale,
        max_nfev=300,
        xtol=1e-10,
        ftol=1e-10,
        gtol=1e-10,
    )
    params = np.r_[rotvec, result.x]
    return params, float(np.sum(residual_vector(params, source, target) ** 2)), int(result.nfev), bool(result.success)


def estimate(
    source: list[dict], target: list[dict], loss: str = "soft_l1", f_scale: float = 0.05
) -> dict:
    """Register paired source/target planes; returns rotation, translation and cost."""
    normals_s = np.asarray([s["normal"] for s in source], dtype=float)
    normals_t = np.asarray([t["normal"] for t in target], dtype=float)
    r0 = _rotation_initial(normals_s, normals_t)
    t0 = fit_translation_linear(source, target, r0)
    x0 = np.r_[_matrix_to_rotvec(r0), t0]
    result = least_squares(
        residual_vector,
        x0,
        args=(source, target),
        loss=loss,
        f_scale=f_scale,
        max_nfev=500,
        xtol=1e-10,
        ftol=1e-10,
        gtol=1e-10,
    )
    r_refined = _rotvec_to_matrix(result.x[:3])
    t_linear = fit_translation_linear(source, target, r_refined)
    fixed_params, fixed_cost, _, _ = _solve_with_fixed_rotation(
        r_refined, t_linear, source, target, loss, f_scale
    )
    full_cost = float(np.sum(residual_vector(result.x, source, target) ** 2))
    params = fixed_params if fixed_cost <= full_cost else result.x
    return {
        "rotation": _rotvec_to_matrix(params[:3]).tolist(),
        "translation": params[3:6].tolist(),
        "cost": min(full_cost, fixed_cost),
    }


def run(problems_path: Path, predictions_path: Path) -> None:
    """Solver contract: read a problems file, write one pose per instance id."""
    instances = json.loads(problems_path.read_text())["instances"]
    predictions = {}
    for instance in instances:
        pose = estimate(instance["source"], instance["target"])
        predictions[instance["id"]] = {"rotation": pose["rotation"], "translation": pose["translation"]}
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.write_text(json.dumps({"method": "grassmann_refine", "predictions": predictions}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Affine-Grassmannian plane-to-plane registration solver.")
    parser.add_argument("--problems", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    run(args.problems, args.predictions)


if __name__ == "__main__":
    main()
