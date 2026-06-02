from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np


SLICE = "test"
SPLIT_INDICES = (1, 3, 5, 7, 9, 11)
OUTLIER_RE = re.compile(r"_outlier_\d+\.\d+$")
SUITE_SPECS = (
    (
        "synthetic_plane_registration_clean",
        Path("data/plane_registration_outlier_0.00.json"),
        "_outlier_0.00",
    ),
    (
        "synthetic_plane_registration",
        Path("data/plane_registration_outlier_0.05.json"),
        "_outlier_0.05",
    ),
    (
        "synthetic_plane_registration_outlier_0.10",
        Path("data/plane_registration_outlier_0.10.json"),
        "_outlier_0.10",
    ),
)


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("zero-length vector")
    return v / n


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    return json.loads(path.read_text())


def _prediction_method(path: Path) -> str:
    pred = _load_json(path)
    method = pred.get("method")
    if not isinstance(method, str) or not method:
        raise ValueError(f"{path} must contain a non-empty string 'method'")
    return method


def _dedupe_predictions(predictions: list[Path]) -> list[Path]:
    by_method: dict[str, Path] = {}
    for path in predictions:
        method = _prediction_method(path)
        if method in by_method:
            raise ValueError(
                f"duplicate predictions for method '{method}': "
                f"{by_method[method]} and {path}"
            )
        by_method[method] = path
    return [by_method[name] for name in sorted(by_method)]


def _scores_methods(scores_path: Path, experiment: str | None = None) -> set[str]:
    if not scores_path.exists():
        return set()
    data = _load_json(scores_path)
    experiments = data.get("experiments", data)
    method_names: set[str] = set()
    for exp_name, exp_payload in experiments.items():
        if str(exp_name).startswith("_"):
            continue
        if experiment is not None and exp_name != experiment:
            continue
        if not isinstance(exp_payload, dict):
            continue
        results = exp_payload.get("results", exp_payload)
        if not isinstance(results, dict):
            continue
        method_names.update(
            name for name in results
            if isinstance(name, str) and not name.startswith("_")
        )
    return method_names


def _filter_to_required_methods(predictions: list[Path], required: set[str]) -> list[Path]:
    if not required:
        return _dedupe_predictions(predictions)
    by_method = {_prediction_method(path): path for path in predictions}
    missing = sorted(required - set(by_method))
    if missing:
        raise FileNotFoundError(
            "missing held-out prediction file(s) for train-scored method(s): "
            + ", ".join(missing)
        )
    return [by_method[name] for name in sorted(required)]


def discover_single_predictions(
    checkpoints_dir: Path,
    train_scores: Path,
) -> list[Path]:
    generic = [
        path
        for path in checkpoints_dir.glob("*.json")
        if not OUTLIER_RE.search(path.stem)
    ]
    candidates = generic or sorted(checkpoints_dir.glob("*_outlier_0.05.json"))
    if not candidates:
        raise FileNotFoundError(f"no prediction JSON files found in {checkpoints_dir}")
    return _filter_to_required_methods(candidates, _scores_methods(train_scores))


def discover_suite_predictions(
    checkpoints_dir: Path,
    suffix: str,
    train_scores: Path,
    experiment: str,
) -> list[Path]:
    predictions = sorted(checkpoints_dir.glob(f"*{suffix}.json"))
    if not predictions:
        raise FileNotFoundError(
            f"no prediction JSON files matching '*{suffix}.json' in {checkpoints_dir}"
        )
    return _filter_to_required_methods(
        predictions,
        _scores_methods(train_scores, experiment),
    )


def _rotation_normal_error_deg(
    r_est: np.ndarray,
    source_normals: list[np.ndarray],
    target_normals: list[np.ndarray],
) -> float:
    errors = []
    for n_source, n_target in zip(source_normals, target_normals):
        moved = _unit(r_est @ n_source)
        target = _unit(n_target)
        cosine = abs(float(moved @ target))
        errors.append(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
    return float(np.sqrt(np.mean(np.square(errors))))


def _projected_translation_error_percent(
    t_est: np.ndarray,
    t_gt: np.ndarray,
    target_normals: list[np.ndarray],
) -> float:
    t_delta = t_est - t_gt
    projected = [float(_unit(n_target) @ t_delta) for n_target in target_normals]
    rmse = float(np.sqrt(np.mean(np.square(projected))))
    # The split sees only scalar plane-normal components.  sqrt(3) converts
    # isotropic projected RMSE back to a 3-D translation-norm estimate.
    return rmse * math.sqrt(3.0) / max(float(np.linalg.norm(t_gt)), 1e-12) * 100.0


def evaluate_one(data_path: Path, predictions: list[Path], indices: tuple[int, ...]) -> dict:
    data = _load_json(data_path)
    t_gt = np.asarray(data["ground_truth"]["translation"], dtype=float)
    source = data["source"]
    target = data["target"]
    if max(indices) >= len(source) or max(indices) >= len(target):
        raise ValueError(f"split indices exceed plane count in {data_path}")

    source_normals = [
        np.asarray(source[i]["normal"], dtype=float)
        for i in indices
    ]
    target_normals = [
        np.asarray(target[i]["normal"], dtype=float)
        for i in indices
    ]

    results = {}
    for path in _dedupe_predictions(predictions):
        pred = _load_json(path)
        method = pred["method"]
        r_est = np.asarray(pred["rotation"], dtype=float)
        t_est = np.asarray(pred["translation"], dtype=float)
        results[method] = {
            "translation_error_percent": _projected_translation_error_percent(
                t_est, t_gt, target_normals
            ),
            "rotation_error_deg": _rotation_normal_error_deg(
                r_est, source_normals, target_normals
            ),
            "num_planes": float(len(indices)),
        }
    return results


def evaluate(
    data_path: Path,
    predictions: list[Path],
    output: Path,
) -> None:
    payload = {
        "_slice": SLICE,
        "experiments": {
            "synthetic_plane_registration": {
                "slice": SLICE,
                "split_indices": list(SPLIT_INDICES),
                "results": evaluate_one(data_path, predictions, SPLIT_INDICES),
            }
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2))


def evaluate_suite(output: Path, checkpoints_dir: Path, train_scores: Path) -> None:
    experiments = {}
    for name, data_path, suffix in SUITE_SPECS:
        experiments[name] = {
            "slice": SLICE,
            "split_indices": list(SPLIT_INDICES),
            "results": evaluate_one(
                data_path,
                discover_suite_predictions(checkpoints_dir, suffix, train_scores, name),
                SPLIT_INDICES,
            ),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"_slice": SLICE, "experiments": experiments}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/plane_registration.json"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores_test.json"))
    parser.add_argument("--checkpoints-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--train-scores", type=Path, default=Path("scoring/scores_train.json"))
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("predictions", nargs="*", type=Path)
    args = parser.parse_args()

    if args.suite:
        evaluate_suite(args.output, args.checkpoints_dir, args.train_scores)
        return

    predictions = args.predictions or discover_single_predictions(
        args.checkpoints_dir,
        args.train_scores,
    )
    if args.predictions:
        predictions = _filter_to_required_methods(
            predictions,
            _scores_methods(args.train_scores),
        )
    evaluate(args.data, predictions, args.output)


if __name__ == "__main__":
    main()
