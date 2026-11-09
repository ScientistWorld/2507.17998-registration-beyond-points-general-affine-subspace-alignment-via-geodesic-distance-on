"""Visible train evaluator for the plane-registration gym.

Generates the train instances with the public generator
(``data/synthetic_planes.py``) from the visible seed below, runs every solver
registered as ``scripts/solvers/<name>.sh`` (or only the names given on the
command line) on a problems file holding the instance inputs only, validates
each returned pose (finite, proper rotation in SO(3), one pose per instance)
and scores it against the ground truth.  A solver that crashes or returns any
invalid pose is scored as failed: the worst value of every metric.

The hidden test uses the same experiments, sizes, metrics and solver contract
on instances drawn from the same distribution with a different, hidden seed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from data.synthetic_planes import generate_suite  # noqa: E402  (public generator)

SLICE = "train"
ENTROPY = 20260602
EXPERIMENTS = (
    {
        "name": "object_registration",
        "count": 200,
        "outlier_ratios": (0.05, 0.20, 0.35, 0.50),
        "mismatched": (0,),
    },
    {
        "name": "object_registration_mismatched",
        "count": 120,
        "outlier_ratios": (0.05, 0.20, 0.35, 0.50),
        "mismatched": (2, 3, 4),
    },
)
SOLVER_DIR = ROOT / "scripts" / "solvers"
PROBLEM_FORMAT = "plane-registration-problems/v1"
METRICS = ("translation_error_percent", "rotation_error_deg")
ROTATION_CAP_DEG = 180.0
TRANSLATION_CAP_PERCENT = 100.0
ORTHONORMAL_TOLERANCE = 1e-6
SOLVER_TIMEOUT_SEC = 3 * 3600


def discover_solvers(names: list[str] | None = None) -> list[Path]:
    scripts = sorted(
        path
        for path in SOLVER_DIR.glob("*.sh")
        if path.is_file() and not path.name.startswith(("_", "."))
    )
    if names:
        by_name = {path.stem: path for path in scripts}
        missing = [name for name in names if name not in by_name]
        if missing:
            raise FileNotFoundError(f"unregistered solver(s): {', '.join(missing)} (expected in {SOLVER_DIR})")
        scripts = [by_name[name] for name in names]
    if not scripts:
        raise FileNotFoundError(f"no solver scripts registered in {SOLVER_DIR}")
    return scripts


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _vector3(value):
    if isinstance(value, list) and len(value) == 3 and all(_is_number(v) for v in value):
        return np.asarray(value, dtype=float)
    return None


def _matrix3(value):
    if isinstance(value, list) and len(value) == 3 and all(
        isinstance(row, list) and len(row) == 3 and all(_is_number(v) for v in row) for row in value
    ):
        return np.asarray(value, dtype=float)
    return None


def check_pose(entry):
    """Return ``(R, t)`` for a valid rigid pose, else an error string."""
    if not isinstance(entry, dict):
        return "missing or malformed prediction"
    try:
        rotation = _matrix3(entry.get("rotation"))
        translation = _vector3(entry.get("translation"))
    except (OverflowError, ValueError, TypeError):
        return "unparseable pose"
    if rotation is None:
        return "rotation is not a 3x3 list of numbers"
    if translation is None:
        return "translation is not a list of 3 numbers"
    if not (np.isfinite(rotation).all() and np.isfinite(translation).all()):
        return "non-finite pose"
    # Entries of a rotation lie in [-1, 1]; bounding them first also keeps
    # R^T R from overflowing.  Comparisons are written NaN-safe.
    if not float(np.abs(rotation).max()) <= 1.0 + ORTHONORMAL_TOLERANCE:
        return "rotation has entries outside [-1, 1]"
    ortho = float(np.linalg.norm(rotation.T @ rotation - np.eye(3)))
    if not ortho <= ORTHONORMAL_TOLERANCE:
        return f"rotation is not orthonormal (||R^T R - I||_F = {ortho:.3g})"
    det = float(np.linalg.det(rotation))
    if not det > 0.0:
        return f"rotation is a reflection (det = {det:.3g})"
    return rotation, translation


def rotation_error_deg(r_est: np.ndarray, r_gt: np.ndarray) -> float:
    cosine = float((np.trace(r_est.T @ r_gt) - 1.0) / 2.0)
    if not np.isfinite(cosine):
        return ROTATION_CAP_DEG
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def translation_error_percent(t_est: np.ndarray, t_gt: np.ndarray) -> float:
    error = float(np.linalg.norm(t_est - t_gt) / np.linalg.norm(t_gt) * 100.0)
    if not error <= TRANSLATION_CAP_PERCENT:  # also catches inf/nan from overflow
        return TRANSLATION_CAP_PERCENT
    return error


def run_solver(script: Path, problems: list[dict]):
    """Run one solver on a fresh copy of the inputs; return ``(payload, error)``."""
    with tempfile.TemporaryDirectory(prefix=f"plane_{SLICE}_{script.stem}_") as tmp:
        problems_path = Path(tmp) / "problems.json"
        predictions_path = Path(tmp) / "predictions.json"
        problems_path.write_text(json.dumps({"format": PROBLEM_FORMAT, "instances": problems}))
        try:
            proc = subprocess.run(
                ["bash", str(script), str(problems_path), str(predictions_path)],
                cwd=str(ROOT),
                stdin=subprocess.DEVNULL,
                timeout=SOLVER_TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired:
            return None, f"solver exceeded {SOLVER_TIMEOUT_SEC} s"
        if proc.returncode != 0:
            return None, f"solver exited with code {proc.returncode}"
        if not predictions_path.is_file():
            return None, "solver wrote no predictions file"
        try:
            payload = json.loads(predictions_path.read_text())
        except Exception as exc:  # malformed JSON, encoding, recursion depth
            return None, f"predictions file is not valid JSON ({type(exc).__name__})"
    return payload, None


def score_payload(payload, truths: dict):
    """Per-instance errors, or an error string if any pose is invalid."""
    predictions = payload.get("predictions") if isinstance(payload, dict) else None
    if not isinstance(predictions, dict):
        return None, "predictions file lacks a 'predictions' object"
    per_instance = {}
    for instance_id, truth in truths.items():
        checked = check_pose(predictions.get(instance_id))
        if isinstance(checked, str):
            return None, f"{instance_id}: {checked}"
        rotation, translation = checked
        per_instance[instance_id] = {
            "translation_error_percent": translation_error_percent(
                translation, np.asarray(truth["translation"], dtype=float)
            ),
            "rotation_error_deg": rotation_error_deg(rotation, np.asarray(truth["rotation"], dtype=float)),
        }
    return per_instance, None


def aggregate(per_instance: dict, membership: dict) -> dict:
    out = {}
    for spec in EXPERIMENTS:
        ids = [i for i, m in membership.items() if m["experiment"] == spec["name"]]
        out[spec["name"]] = {
            metric: float(np.mean([per_instance[i][metric] for i in ids])) for metric in METRICS
        }
    return out


def failed_metrics() -> dict:
    return {"translation_error_percent": TRANSLATION_CAP_PERCENT, "rotation_error_deg": ROTATION_CAP_DEG}


def main() -> None:
    parser = argparse.ArgumentParser(description="Score registered solvers on the visible train instances.")
    parser.add_argument("--output", type=Path, default=ROOT / "scoring" / "scores_train.json")
    parser.add_argument("--details", type=Path, default=None, help="optional per-instance error dump (diagnostics)")
    parser.add_argument("--write-problems", type=Path, default=None,
                        help="also write the train problems (inputs) and truths to this directory")
    parser.add_argument("solvers", nargs="*", help="solver names to score (default: every registered solver)")
    args = parser.parse_args()

    problems, truths, membership = generate_suite(ENTROPY, EXPERIMENTS)
    if args.write_problems is not None:
        args.write_problems.mkdir(parents=True, exist_ok=True)
        (args.write_problems / "train_problems.json").write_text(
            json.dumps({"format": PROBLEM_FORMAT, "instances": problems})
        )
        (args.write_problems / "train_truths.json").write_text(
            json.dumps({"truths": truths, "membership": membership})
        )
    solvers = discover_solvers(args.solvers)
    experiments = {
        spec["name"]: {"slice": SLICE, "num_instances": int(spec["count"]), "results": {}} for spec in EXPERIMENTS
    }
    failures: dict[str, str] = {}
    details: dict[str, dict] = {}
    for script in solvers:
        name = script.stem
        print(f"[{SLICE}] running solver '{name}' on {len(problems)} instances", file=sys.stderr, flush=True)
        payload, error = run_solver(script, problems)
        per_instance = None
        if error is None:
            per_instance, error = score_payload(payload, truths)
        if error is not None:
            failures[name] = error
            for exp in experiments.values():
                exp["results"][name] = failed_metrics()
            print(f"[{SLICE}] solver '{name}' FAILED: {error}", file=sys.stderr, flush=True)
            continue
        for exp_name, metrics in aggregate(per_instance, membership).items():
            experiments[exp_name]["results"][name] = metrics
        details[name] = per_instance

    scores = {"_slice": SLICE, "_failed_methods": failures, "experiments": experiments}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2))
    if args.details is not None:
        args.details.parent.mkdir(parents=True, exist_ok=True)
        args.details.write_text(
            json.dumps({"membership": membership, "failures": failures, "methods": details})
        )
    for exp_name, exp in experiments.items():
        for name, metrics in exp["results"].items():
            print(
                f"[{SLICE}] {exp_name:32s} {name:32s} "
                f"t={metrics['translation_error_percent']:.4f}%  R={metrics['rotation_error_deg']:.4f} deg",
                flush=True,
            )


if __name__ == "__main__":
    main()
