"""Run the reference, baselines, variants and shortcuts through the hardened
hidden test, one attempt at a time, and summarise the results.

    python3 redteam/hardening/harness.py run        # resumable
    python3 redteam/hardening/harness.py summarize

For every attempt the harness snapshots ``scripts/solvers``, ``scoring``,
``data`` and ``eval``, registers the attempt as the only solver, runs the
unchanged entry point (``bash scripts/evaluate_test.sh``; honest attempts add
``--details`` for the paired analysis, which does not change scoring), copies
the scores, and restores every snapshotted file.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "redteam" / "hardening" / "results"
SNAPSHOT_DIRS = ("scripts/solvers", "scoring", "data", "eval")
GUARDED = ("eval/test/evaluate.py", "eval/test/hidden_instances.py", "scripts/evaluate_test.sh")

HONEST = {
    "grassmann_refine": "reference",
    "plane_parameter_lstsq": "baseline",
    "better_consensus_refine": "better",
    "better_offset_weighted": "better",
    "better_consensus_offset_weighted": "better",
    "better_robust_geometric": "variant",
    "ablation_linear_init": "ablation",
    "weaker_linear_loss": "weaker",
    "weaker_without_sign_invariance": "weaker",
    "weaker_identity": "weaker",
}
SHORTCUTS = (
    "shortcut_visible_answers",
    "shortcut_nonrigid_fit",
    "shortcut_nonrigid_scale",
    "shortcut_overflow_scale",
    "shortcut_reflection",
    "shortcut_replace_fixed_data",
    "shortcut_partial_regimes",
    "shortcut_self_reported_fields",
    "shortcut_write_scores",
    "shortcut_nan",
    "shortcut_infinity",
    "shortcut_null",
    "shortcut_empty",
    "shortcut_zero_rotation",
    "shortcut_missing_instance",
    "shortcut_crash",
)
TRAIN_ATTEMPTS = (
    "grassmann_refine",
    "plane_parameter_lstsq",
    "better_consensus_refine",
    "better_offset_weighted",
    "better_consensus_offset_weighted",
    "better_robust_geometric",
    "ablation_linear_init",
)
METRICS = ("translation_error_percent", "rotation_error_deg")


def _snapshot() -> dict[str, tuple[bytes, int]]:
    snap = {}
    for rel in SNAPSHOT_DIRS:
        for path in (ROOT / rel).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                snap[str(path.relative_to(ROOT))] = (path.read_bytes(), path.stat().st_mode & 0o777)
    return snap


def _restore(snap: dict[str, tuple[bytes, int]]) -> list[str]:
    changed = []
    for rel in SNAPSHOT_DIRS:
        for path in sorted((ROOT / rel).rglob("*"), reverse=True):
            key = str(path.relative_to(ROOT))
            if path.is_file() and "__pycache__" not in path.parts and key not in snap:
                path.unlink()
                changed.append(key + " (removed)")
    for key, (data, mode) in snap.items():
        path = ROOT / key
        if not path.is_file() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            changed.append(key)
        if path.stat().st_mode & 0o777 != mode:
            path.chmod(mode)
    return changed


def _reset_from_git() -> None:
    """Undo leftovers of an attempt killed mid-run (before a resumed run)."""
    tracked = ["scripts/solvers", "data", "eval"]
    subprocess.run(["git", "checkout", "--", *tracked], cwd=str(ROOT), check=False)
    subprocess.run(["git", "clean", "-fdq", "--", *tracked], cwd=str(ROOT), check=False)


def _hash(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _solver_script(name: str, snap: dict[str, bytes]) -> str:
    header = '#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")/../.."\n'
    if name == "grassmann_refine":
        return header + (
            'python3 method/grassmann.py --problems "$1" --predictions "$2"\n'
            "mkdir -p redteam/hardening/results/_cache\n"
            'cp "$2" "redteam/hardening/results/_cache/grassmann_refine_$(sha1sum "$1" | cut -c1-16).json"\n'
        )
    if name == "plane_parameter_lstsq":
        return snap["scripts/solvers/plane_parameter_lstsq.sh"][0].decode()
    return header + f'exec python3 redteam/hardening/variants.py {name} "$1" "$2"\n'


def run_attempt(name: str, split: str) -> None:
    out_dir = RESULTS / name
    if (out_dir / f"status_{split}.json").is_file():
        print(f"skip {name} [{split}] (done)", flush=True)
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    snap = _snapshot()
    guarded_before = {rel: _hash(rel) for rel in GUARDED}
    cmd = ["bash", f"scripts/evaluate_{split}.sh"]
    if name in HONEST:
        cmd += ["--details", str(out_dir / f"details_{split}.json")]
    try:
        solver_dir = ROOT / "scripts" / "solvers"
        for path in solver_dir.glob("*.sh"):
            path.unlink()
        script = solver_dir / f"{name}.sh"
        script.write_text(_solver_script(name, snap))
        script.chmod(0o755)
        print(f"run {name} [{split}]: {' '.join(cmd)}", flush=True)
        start = time.time()
        with open(out_dir / f"{split}.log", "w") as log:
            proc = subprocess.run(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
        seconds = time.time() - start
        scores_file = ROOT / "scoring" / f"scores_{split}.json"
        if proc.returncode == 0 and scores_file.is_file():
            shutil.copy2(scores_file, out_dir / f"scores_{split}.json")
        guarded_after_run = {rel: _hash(rel) for rel in GUARDED}
    finally:
        changed = _restore(snap)
    status = {
        "attempt": name,
        "split": split,
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "seconds": round(seconds, 1),
        "files_changed_during_run_then_restored": changed,
        "hidden_test_files_modified_during_run": sorted(
            rel for rel in GUARDED if guarded_before[rel] != guarded_after_run[rel]
        ),
    }
    (out_dir / f"status_{split}.json").write_text(json.dumps(status, indent=2))
    print(f"done {name} [{split}] rc={proc.returncode} in {seconds:.0f}s", flush=True)


def run_all() -> None:
    _reset_from_git()
    order = [(n, "test") for n in HONEST] + [(n, "test") for n in SHORTCUTS] + [(n, "train") for n in TRAIN_ATTEMPTS]
    for name, split in order:
        try:
            run_attempt(name, split)
        except Exception as exc:  # keep going; the status file records nothing
            print(f"ERROR {name} [{split}]: {exc!r}", flush=True)


# ------------------------------------------------------------- summary
def _load(path: Path):
    return json.loads(path.read_text()) if path.is_file() else None


def _method_scores(scores: dict, name: str) -> dict | None:
    out = {}
    for exp, payload in scores["experiments"].items():
        res = payload["results"].get(name)
        if res is None:
            return None
        out[exp] = res
    return out


def summarize() -> None:
    ref_json = json.loads((ROOT / "scoring" / "reference.json").read_text())["experiments"]
    exps = list(ref_json)
    attempts = {}
    for name in list(HONEST) + list(SHORTCUTS):
        scores = _load(RESULTS / name / "scores_test.json")
        status = _load(RESULTS / name / "status_test.json")
        if scores is None:
            attempts[name] = {"status": status, "test": None}
            continue
        attempts[name] = {
            "category": HONEST.get(name, "shortcut"),
            "status": status,
            "failed": scores.get("_failed_methods", {}).get(name),
            "test": _method_scores(scores, name),
            "train": None,
        }
        train = _load(RESULTS / name / "scores_train.json")
        if train is not None:
            attempts[name]["train"] = _method_scores(train, name)

    ref = attempts.get("grassmann_refine", {}).get("test")
    if ref is None:
        raise SystemExit("reference attempt has no test scores; nothing to summarise")
    scored = {n: a for n, a in attempts.items() if a.get("test")}
    honest_names = [n for n in scored if n in HONEST]

    def stds(names):
        return {
            e: {m: float(np.std([scored[n]["test"][e][m] for n in names])) for m in METRICS} for e in exps
        }

    def delta(x, s):
        total = 0.0
        for e in exps:
            w = ref_json[e]["weight"]
            for m in METRICS:
                c = abs(ref_json[e]["metrics"][m]["coefficient"])
                sign = 1.0 if ref_json[e]["metrics"][m]["higher_is_better"] else -1.0
                if s[e][m] > 0:
                    total += w * c * sign * (x[e][m] - ref[e][m]) / s[e][m]
        return total

    s_all, s_honest = stds(list(scored)), stds(honest_names)
    for name, a in scored.items():
        a["delta_score_all_cohort"] = delta(a["test"], s_all)
        if name in HONEST:
            a["delta_score_honest_cohort"] = delta(a["test"], s_honest)

    # Paired bootstrap against the reference on identical instances.
    ref_details = _load(RESULTS / "grassmann_refine" / "details_test.json")
    paired = {}
    if ref_details is not None and "grassmann_refine" not in ref_details.get("methods", {}):
        ref_details = None
    if ref_details is not None:
        membership = ref_details["membership"]
        ref_inst = ref_details["methods"]["grassmann_refine"]
        ids = {e: sorted(i for i, m in membership.items() if m["experiment"] == e) for e in exps}
        rng = np.random.default_rng(0)
        boots = {e: rng.integers(0, len(ids[e]), size=(4000, len(ids[e]))) for e in exps}
        for name in honest_names:
            det = _load(RESULTS / name / "details_test.json")
            if det is None or name not in det["methods"] or name == "grassmann_refine":
                continue
            inst = det["methods"][name]
            entry = {}
            comp = np.zeros(4000)
            for e in exps:
                for m in METRICS:
                    d = np.array([inst[i][m] - ref_inst[i][m] for i in ids[e]])
                    bm = d[boots[e]].mean(axis=1)
                    entry[f"{e}/{m}"] = {
                        "mean_diff": float(d.mean()),
                        "ci95": [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))],
                        "frac_instances_better": float(np.mean(d < 0)),
                    }
                    w = ref_json[e]["weight"] * abs(ref_json[e]["metrics"][m]["coefficient"])
                    if s_honest[e][m] > 0:
                        comp += -w * bm / s_honest[e][m]
            entry["delta_score_honest_cohort_ci95"] = [float(np.percentile(comp, 2.5)), float(np.percentile(comp, 97.5))]
            paired[name] = entry

    # Breakdown by regime for honest attempts.
    breakdown = {}
    if ref_details is not None:
        membership = ref_details["membership"]
        for name in honest_names:
            det = _load(RESULTS / name / "details_test.json")
            if det is None or name not in det["methods"]:
                continue
            inst = det["methods"][name]
            groups = {}
            for i, m in membership.items():
                key = f"{m['experiment']}|ratio={m['outlier_ratio']:.2f}|k={m['mismatched']}"
                groups.setdefault(key, []).append(i)
            breakdown[name] = {
                key: {mm: float(np.mean([inst[i][mm] for i in g])) for mm in METRICS} | {"n": len(g)}
                for key, g in sorted(groups.items())
            }

    summary = {
        "reference": ref,
        "cohort_std_all": s_all,
        "cohort_std_honest": s_honest,
        "attempts": attempts,
        "paired_vs_reference": paired,
        "regime_breakdown": breakdown,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))

    lines = ["| attempt | category | failed | " + " | ".join(f"{e} T% | {e} R°" for e in exps)
             + " | ΔS (honest cohort) | ΔS (all) |",
             "|---|---|---|" + "---:|" * (2 * len(exps) + 2)]
    for name, a in scored.items():
        vals = " | ".join(
            f"{a['test'][e]['translation_error_percent']:.4f} | {a['test'][e]['rotation_error_deg']:.4f}" for e in exps
        )
        dh = a.get("delta_score_honest_cohort")
        lines.append(
            f"| {name} | {a['category']} | {'yes' if a['failed'] else 'no'} | {vals} | "
            f"{'' if dh is None else f'{dh:+.4f}'} | {a['delta_score_all_cohort']:+.4f} |"
        )
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    for name, entry in paired.items():
        print(name, json.dumps(entry))


if __name__ == "__main__":
    {"run": run_all, "summarize": summarize}[sys.argv[1]]()
