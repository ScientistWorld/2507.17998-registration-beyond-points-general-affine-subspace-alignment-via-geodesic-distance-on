from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("zero-length vector")
    return v / n


def rotation_error_deg(r_est: np.ndarray, r_gt: np.ndarray) -> float:
    val = (np.trace(r_est.T @ r_gt) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(val, -1.0, 1.0))))


def translation_error_percent(t_est: np.ndarray, t_gt: np.ndarray) -> float:
    return float(np.linalg.norm(t_est - t_gt) / max(np.linalg.norm(t_gt), 1e-12) * 100.0)


def plane_offset_rmse(r_est: np.ndarray, t_est: np.ndarray, source: list[dict], target: list[dict]) -> float:
    residuals = []
    for src, dst in zip(source, target):
        n_source = _unit(np.asarray(src["normal"], dtype=float))
        source_displacement = np.asarray(src["displacement"], dtype=float)
        n_moved = _unit(r_est @ n_source)
        moved_displacement = r_est @ source_displacement + np.outer(n_moved, n_moved) @ t_est

        n_target = _unit(np.asarray(dst["normal"], dtype=float))
        target_displacement = np.asarray(dst["displacement"], dtype=float)
        residuals.append(float(n_target @ (moved_displacement - target_displacement)))
    return float(np.sqrt(np.mean(np.square(residuals))))


def evaluate_one(data_path: Path, predictions: list[Path]) -> dict:
    if not data_path.exists():
        raise FileNotFoundError(f"missing evaluation data: {data_path}")
    missing = [str(path) for path in predictions if not path.exists()]
    if missing:
        raise FileNotFoundError("missing prediction file(s): " + ", ".join(missing))
    data = json.loads(data_path.read_text())
    r_gt = np.asarray(data["ground_truth"]["rotation"], dtype=float)
    t_gt = np.asarray(data["ground_truth"]["translation"], dtype=float)
    source = data["source"]
    target = data["target"]
    results = {}
    for path in predictions:
        pred = json.loads(path.read_text())
        name = pred["method"]
        r = np.asarray(pred["rotation"], dtype=float)
        t = np.asarray(pred["translation"], dtype=float)
        results[name] = {
            "rotation_error_deg": rotation_error_deg(r, r_gt),
            "translation_error_percent": translation_error_percent(t, t_gt),
            "plane_offset_rmse": plane_offset_rmse(r, t, source, target),
            "num_planes": float(len(source)),
        }
    return results


def evaluate(data_path: Path, predictions: list[Path], output: Path) -> None:
    results = evaluate_one(data_path, predictions)
    payload = {"experiments": {"synthetic_plane_registration": {"results": results}}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2))


def evaluate_suite(output: Path) -> None:
    specs = [
        (
            "synthetic_plane_registration_clean",
            Path("data/plane_registration_outlier_0.00.json"),
            [
                Path("checkpoints/plane_parameter_lstsq_outlier_0.00.json"),
                Path("checkpoints/grassmann_refine_outlier_0.00.json"),
            ],
        ),
        (
            "synthetic_plane_registration",
            Path("data/plane_registration_outlier_0.05.json"),
            [
                Path("checkpoints/plane_parameter_lstsq_outlier_0.05.json"),
                Path("checkpoints/grassmann_refine_outlier_0.05.json"),
            ],
        ),
        (
            "synthetic_plane_registration_outlier_0.10",
            Path("data/plane_registration_outlier_0.10.json"),
            [
                Path("checkpoints/plane_parameter_lstsq_outlier_0.10.json"),
                Path("checkpoints/grassmann_refine_outlier_0.10.json"),
            ],
        ),
    ]
    experiments = {}
    for name, data_path, preds in specs:
        results = evaluate_one(data_path, preds)
        experiments[name] = {"results": results}
    if not experiments:
        evaluate(Path("data/plane_registration.json"), [
            Path("checkpoints/plane_parameter_lstsq.json"),
            Path("checkpoints/grassmann_refine.json"),
        ], output)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"experiments": experiments}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("predictions", nargs="*", type=Path)
    args = parser.parse_args()
    if args.suite:
        evaluate_suite(args.output)
        return
    preds = args.predictions or [
        Path("checkpoints/plane_parameter_lstsq.json"),
        Path("checkpoints/grassmann_refine.json"),
    ]
    evaluate(args.data, preds, args.output)


if __name__ == "__main__":
    main()
