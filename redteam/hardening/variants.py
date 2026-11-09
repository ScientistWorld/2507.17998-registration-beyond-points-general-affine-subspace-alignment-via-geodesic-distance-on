"""Variant and shortcut solvers used to check the hardened gym.

Each attempt is installed by ``harness.py`` as the only file in
``scripts/solvers/`` and then scored through the unchanged hidden-test entry
point.  Usage (the solver contract):

    python3 redteam/hardening/variants.py <attempt> <problems.json> <predictions.json>

Honest variants use only the instance inputs.  Shortcuts deliberately try to
game the scorer; they exist to show what the evaluator now rejects.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "method"))
sys.path.insert(0, str(ROOT / "baseline"))
import grassmann  # noqa: E402  method/grassmann.py
import plane_parameter  # noqa: E402  baseline/plane_parameter.py

CACHE = ROOT / "redteam" / "hardening" / "results" / "_cache"


# ----------------------------------------------------------------- helpers
def _unit_rows(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def _pose(r, t) -> dict:
    return {"rotation": np.asarray(r, dtype=float).tolist(), "translation": np.asarray(t, dtype=float).tolist()}


def _arrays(inst: dict):
    ns = _unit_rows([p["normal"] for p in inst["source"]])
    nt = _unit_rows([p["normal"] for p in inst["target"]])
    cs = np.asarray([p["displacement"] for p in inst["source"]], dtype=float)
    ct = np.asarray([p["displacement"] for p in inst["target"]], dtype=float)
    return ns, nt, cs, ct


def reference_predictions(problems_path: Path, instances: list[dict]) -> dict:
    """The registered reference's poses (cached by problems-file hash)."""
    key = hashlib.sha1(Path(problems_path).read_bytes()).hexdigest()[:16]
    cache = CACHE / f"grassmann_refine_{key}.json"
    if cache.is_file():
        return json.loads(cache.read_text())["predictions"]
    preds = {}
    for inst in instances:
        est = grassmann.estimate(inst["source"], inst["target"])
        preds[inst["id"]] = _pose(est["rotation"], est["translation"])
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"predictions": preds}))
    return preds


# ------------------------------------------------------- honest variants
def consensus_inliers(ns: np.ndarray, nt: np.ndarray, max_angle_deg: float = 5.0) -> np.ndarray:
    """Sign-invariant inlier-set maximisation over plane correspondences.

    Every pair of correspondences and every sign choice gives a rotation
    hypothesis; the hypothesis aligning the most normals within
    ``max_angle_deg`` (ties: smallest squared angle sum) defines the inliers.
    """
    n = len(ns)
    cos_thr = np.cos(np.radians(max_angle_deg))
    best_key, best_mask = None, np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(i + 1, n):
            a3 = np.cross(ns[i], ns[j])
            if np.linalg.norm(a3) < 1e-9:
                continue
            for si in (1.0, -1.0):
                for sj in (1.0, -1.0):
                    b3 = np.cross(si * nt[i], sj * nt[j])
                    if np.linalg.norm(b3) < 1e-9:
                        continue
                    a = np.stack([ns[i], ns[j], a3 / np.linalg.norm(a3)])
                    b = np.stack([si * nt[i], sj * nt[j], b3 / np.linalg.norm(b3)])
                    r = grassmann._kabsch(a, b)
                    dots = np.abs(np.sum((ns @ r.T) * nt, axis=1))
                    mask = dots >= cos_thr
                    cost = float(np.sum(np.arccos(np.clip(dots[mask], 0.0, 1.0)) ** 2))
                    key = (int(mask.sum()), -cost)
                    if best_key is None or key > best_key:
                        best_key, best_mask = key, mask
    return best_mask


def _offset_weighted_residual(params, source, target, weights):
    """Eq. (7) residuals with each displacement term scaled by (1 + |c_t|^2).

    Per plane, residual_vector stacks two 3-D direction residuals and one 4-D
    embedded-displacement residual (10 entries).
    """
    res = grassmann.residual_vector(params, source, target).reshape(len(source), 10)
    res[:, 6:] *= weights[:, None]
    return res.ravel()


def offset_weighted_estimate(source: list[dict], target: list[dict]) -> np.ndarray:
    ns = np.asarray([s["normal"] for s in source], dtype=float)
    nt = np.asarray([t["normal"] for t in target], dtype=float)
    weights = 1.0 + np.sum(np.asarray([t["displacement"] for t in target], dtype=float) ** 2, axis=1)
    r0 = grassmann._rotation_initial(ns, nt)
    t0 = grassmann.fit_translation_linear(source, target, r0)
    fit = least_squares(
        _offset_weighted_residual, np.r_[Rotation.from_matrix(r0).as_rotvec(), t0],
        args=(source, target, weights), loss="soft_l1", f_scale=0.05,
        max_nfev=500, xtol=1e-10, ftol=1e-10, gtol=1e-10,
    )
    return fit.x


def v_better_consensus_refine(inst: dict) -> dict:
    ns, nt, _, _ = _arrays(inst)
    mask = consensus_inliers(ns, nt)
    if mask.sum() < 3:
        mask[:] = True
    idx = np.flatnonzero(mask)
    est = grassmann.estimate([inst["source"][i] for i in idx], [inst["target"][i] for i in idx])
    return _pose(est["rotation"], est["translation"])


def v_better_offset_weighted(inst: dict) -> dict:
    x = offset_weighted_estimate(inst["source"], inst["target"])
    return _pose(Rotation.from_rotvec(x[:3]).as_matrix(), x[3:])


def v_better_consensus_offset_weighted(inst: dict) -> dict:
    ns, nt, _, _ = _arrays(inst)
    mask = consensus_inliers(ns, nt)
    if mask.sum() < 3:
        mask[:] = True
    idx = np.flatnonzero(mask)
    x = offset_weighted_estimate([inst["source"][i] for i in idx], [inst["target"][i] for i in idx])
    return _pose(Rotation.from_rotvec(x[:3]).as_matrix(), x[3:])


def v_better_robust_geometric(inst: dict) -> dict:
    """Iteration-10 red-team variant: sign-aligned joint normal/offset fit."""
    ns, nt, cs, ct = _arrays(inst)
    r0 = grassmann._rotation_initial(ns, nt)
    sign = np.where(np.sum((ns @ r0.T) * nt, axis=1) < 0, -1.0, 1.0)
    nt = nt * sign[:, None]
    offsets_s = np.sum(ns * cs, axis=1)
    offsets_t = np.sum(nt * ct, axis=1)
    t0 = np.linalg.lstsq(nt, offsets_t - offsets_s, rcond=None)[0]

    def residual(x):
        r = Rotation.from_rotvec(x[:3]).as_matrix()
        return np.r_[(ns @ r.T - nt).ravel(), nt @ x[3:] + offsets_s - offsets_t]

    fit = least_squares(residual, np.r_[Rotation.from_matrix(r0).as_rotvec(), t0], loss="soft_l1",
                        f_scale=0.1, max_nfev=1000, ftol=1e-12, xtol=1e-12, gtol=1e-12)
    return _pose(Rotation.from_rotvec(fit.x[:3]).as_matrix(), fit.x[3:])


def v_ablation_linear_init(inst: dict) -> dict:
    """The reference's own sign-invariant linear initialiser, no refinement."""
    ns, nt, _, _ = _arrays(inst)
    r0 = grassmann._rotation_initial(ns, nt)
    return _pose(r0, grassmann.fit_translation_linear(inst["source"], inst["target"], r0))


def v_weaker_linear_loss(inst: dict) -> dict:
    est = grassmann.estimate(inst["source"], inst["target"], loss="linear")
    return _pose(est["rotation"], est["translation"])


def v_weaker_without_sign_invariance(inst: dict) -> dict:
    r, t = plane_parameter.estimate(inst)
    return _pose(r, t)


def v_weaker_identity(inst: dict) -> dict:
    return _pose(np.eye(3), np.zeros(3))


PER_INSTANCE = {
    "better_consensus_refine": v_better_consensus_refine,
    "better_offset_weighted": v_better_offset_weighted,
    "better_consensus_offset_weighted": v_better_consensus_offset_weighted,
    "better_robust_geometric": v_better_robust_geometric,
    "ablation_linear_init": v_ablation_linear_init,
    "weaker_linear_loss": v_weaker_linear_loss,
    "weaker_without_sign_invariance": v_weaker_without_sign_invariance,
    "weaker_identity": v_weaker_identity,
}


# -------------------------------------------------------------- shortcuts
def _fingerprint(inst: dict) -> tuple:
    return tuple(np.round(np.asarray([p["displacement"] for p in inst["target"]], dtype=float).ravel(), 9))


def s_visible_answers(problems_path: Path, instances: list[dict]) -> dict:
    """Copy any answer the instance carries, else look it up among the visible
    train instances regenerated from the visible seed (seed replay)."""
    spec = importlib.util.spec_from_file_location("visible_train_eval", ROOT / "eval" / "train" / "evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems, truths, _ = module.generate_suite(module.ENTROPY, module.EXPERIMENTS)
    lookup = {_fingerprint(p): truths[p["id"]] for p in problems}
    preds, hits = {}, 0
    for inst in instances:
        answer = inst.get("ground_truth") or lookup.get(_fingerprint(inst))
        if answer is not None:
            hits += 1
            preds[inst["id"]] = _pose(answer["rotation"], answer["translation"])
        else:
            preds[inst["id"]] = _pose(np.eye(3), np.zeros(3))
    print(f"shortcut_visible_answers: answers found for {hits}/{len(instances)} instances", file=sys.stderr)
    return preds


def s_nonrigid_fit(problems_path: Path, instances: list[dict]) -> dict:
    """Unrestricted 3x3 map fitted to sign-aligned normals; reference translation."""
    ref = reference_predictions(problems_path, instances)
    preds = {}
    for inst in instances:
        ns, nt, _, _ = _arrays(inst)
        r0 = np.asarray(ref[inst["id"]]["rotation"])
        sign = np.where(np.sum((ns @ r0.T) * nt, axis=1) < 0, -1.0, 1.0)
        m = np.linalg.lstsq(ns, nt * sign[:, None], rcond=None)[0].T
        preds[inst["id"]] = _pose(m, ref[inst["id"]]["translation"])
    return preds


def _map_reference(problems_path: Path, instances: list[dict], fn) -> dict:
    ref = reference_predictions(problems_path, instances)
    return {
        i: _pose(fn(np.asarray(p["rotation"])), p["translation"]) for i, p in ref.items()
    }


def s_nonrigid_scale(problems_path, instances):
    return _map_reference(problems_path, instances, lambda r: 1.001 * r)


def s_overflow_scale(problems_path, instances):
    """Finite but huge entries: R^T R overflows to NaN in a naive check."""
    return _map_reference(problems_path, instances, lambda r: 1e200 * r)


def s_reflection(problems_path, instances):
    return _map_reference(problems_path, instances, lambda r: r @ np.diag([1.0, 1.0, -1.0]))


def s_replace_fixed_data(problems_path: Path, instances: list[dict]) -> dict:
    """Rewrite the generators so targets equal sources and the truth is identity,
    then answer identity.  The harness restores both files afterwards."""
    patch = (
        "\n\n_original_generate_instance = generate_instance\n"
        "def generate_instance(rng, outlier_ratio, n_mismatched=0):\n"
        "    problem, _ = _original_generate_instance(rng, outlier_ratio, n_mismatched)\n"
        "    problem['target'] = problem['source']\n"
        "    return problem, {'rotation': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],"
        " 'translation': [1.0, 0.0, 0.0]}\n"
    )
    for rel in ("data/synthetic_planes.py", "eval/test/hidden_instances.py"):
        path = ROOT / rel
        if path.is_file():
            path.write_text(path.read_text() + patch)
    return {inst["id"]: _pose(np.eye(3), [1.0, 0.0, 0.0]) for inst in instances}


def s_partial_regimes(problems_path: Path, instances: list[dict]) -> dict:
    """Reference on half of the instances, identity on the other half."""
    ref = reference_predictions(problems_path, instances)
    return {
        inst["id"]: (ref[inst["id"]] if k % 2 == 0 else _pose(np.eye(3), np.zeros(3)))
        for k, inst in enumerate(instances)
    }


def s_self_reported_fields(problems_path: Path, instances: list[dict]) -> dict:
    preds = {}
    for inst in instances:
        entry = _pose(np.eye(3), np.zeros(3))
        entry.update({"translation_error_percent": -1e12, "rotation_error_deg": -1e12, "cost": -1e12,
                      "success": True, "valid": True, "score": 1e12})
        preds[inst["id"]] = entry
    return preds


def s_write_scores(problems_path: Path, instances: list[dict]) -> dict:
    fake = {"experiments": {name: {"results": {"shortcut_write_scores": {
        "translation_error_percent": -1e12, "rotation_error_deg": -1e12}}}
        for name in ("object_registration", "object_registration_mismatched")}}
    for rel in ("scoring/scores_test.json", "scoring/scores_train.json", "scoring/scores.json"):
        (ROOT / rel).write_text(json.dumps(fake))
    return {inst["id"]: _pose(np.eye(3), np.zeros(3)) for inst in instances}


def _constant(rotation, translation):
    def fn(problems_path, instances):
        return {inst["id"]: {"rotation": rotation, "translation": translation} for inst in instances}
    return fn


def s_missing_instance(problems_path: Path, instances: list[dict]) -> dict:
    ref = reference_predictions(problems_path, instances)
    ref.pop(instances[0]["id"], None)
    return ref


def s_crash(problems_path: Path, instances: list[dict]) -> dict:
    raise SystemExit(1)


_NAN = [[float("nan")] * 3 for _ in range(3)]
_INF = [[float("inf")] * 3 for _ in range(3)]
WHOLE_SUITE = {
    "shortcut_visible_answers": s_visible_answers,
    "shortcut_nonrigid_fit": s_nonrigid_fit,
    "shortcut_nonrigid_scale": s_nonrigid_scale,
    "shortcut_overflow_scale": s_overflow_scale,
    "shortcut_reflection": s_reflection,
    "shortcut_replace_fixed_data": s_replace_fixed_data,
    "shortcut_partial_regimes": s_partial_regimes,
    "shortcut_self_reported_fields": s_self_reported_fields,
    "shortcut_write_scores": s_write_scores,
    "shortcut_nan": _constant(_NAN, [0.0, 0.0, 0.0]),
    "shortcut_infinity": _constant(_INF, [0.0, 0.0, 0.0]),
    "shortcut_null": _constant(None, None),
    "shortcut_empty": _constant([], []),
    "shortcut_zero_rotation": _constant([[0.0] * 3 for _ in range(3)], [0.0, 0.0, 0.0]),
    "shortcut_missing_instance": s_missing_instance,
    "shortcut_crash": s_crash,
}


def main() -> None:
    attempt, problems_path, predictions_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    payload = json.loads(problems_path.read_text())
    instances = payload["instances"]
    if attempt in PER_INSTANCE:
        fn = PER_INSTANCE[attempt]
        preds = {inst["id"]: fn(inst) for inst in instances}
    elif attempt in WHOLE_SUITE:
        preds = WHOLE_SUITE[attempt](problems_path, instances)
    else:
        raise SystemExit(f"unknown attempt {attempt}")
    out = {"method": attempt, "predictions": preds}
    if attempt == "shortcut_self_reported_fields":
        out.update({"translation_error_percent": -1e12, "rotation_error_deg": -1e12, "all_valid": True})
    predictions_path.write_text(json.dumps(out))


if __name__ == "__main__":
    main()
