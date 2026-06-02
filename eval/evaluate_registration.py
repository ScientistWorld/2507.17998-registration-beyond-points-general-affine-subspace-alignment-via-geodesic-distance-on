from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def rotation_error_deg(r_est: np.ndarray, r_gt: np.ndarray) -> float:
    val = (np.trace(r_est.T @ r_gt) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(val, -1.0, 1.0))))


def translation_error_percent(t_est: np.ndarray, t_gt: np.ndarray) -> float:
    return float(np.linalg.norm(t_est - t_gt) / max(np.linalg.norm(t_gt), 1e-12) * 100.0)


def evaluate(data_path: Path, predictions: list[Path], output: Path) -> None:
    data = json.loads(data_path.read_text())
    r_gt = np.asarray(data["ground_truth"]["rotation"], dtype=float)
    t_gt = np.asarray(data["ground_truth"]["translation"], dtype=float)
    results = {}
    for path in predictions:
        if not path.exists():
            continue
        pred = json.loads(path.read_text())
        name = pred["method"]
        r = np.asarray(pred["rotation"], dtype=float)
        t = np.asarray(pred["translation"], dtype=float)
        results[name] = {
            "rotation_error_deg": rotation_error_deg(r, r_gt),
            "translation_error_percent": translation_error_percent(t, t_gt),
            "num_planes": float(len(data["source"])),
        }
    payload = {"experiments": {"synthetic_plane_registration": {"results": results}}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    parser.add_argument("predictions", nargs="*", type=Path)
    args = parser.parse_args()
    preds = args.predictions or [
        Path("checkpoints/plane_parameter_lstsq.json"),
        Path("checkpoints/grassmann_refine.json"),
    ]
    evaluate(args.data, preds, args.output)


if __name__ == "__main__":
    main()
