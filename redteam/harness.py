"""Audit orchestration; never imported by the evaluator.

Only prepare/before_test install a future attempt's ordinary files. Evaluation
always runs the gym's untouched script with no arguments in another process.
Original small artifacts are saved and restored between attempts.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'
INITIAL = AUDIT / '_initial'
CACHE = AUDIT / '_cache'
RATIOS = ('0.00', '0.05', '0.10')
NAMES = ('synthetic_plane_registration_clean', 'synthetic_plane_registration',
         'synthetic_plane_registration_outlier_0.10')


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=True) + '\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def initialize():
    if (INITIAL / 'manifest.json').exists():
        return
    INITIAL.mkdir(parents=True, exist_ok=True)
    files = [*sorted((ROOT / 'data').glob('*.json')),
             *sorted((ROOT / 'checkpoints').glob('*')),
             *sorted((ROOT / 'scoring').glob('scores*.json'))]
    manifest = []
    for path in files:
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        saved = INITIAL / rel
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, saved)
        manifest.append(str(rel))
    write(INITIAL / 'manifest.json', manifest)
    # This metadata is for the audit's rank calculation only. No candidate
    # implementation reads reference.json or scores_test.json.
    shutil.copy2(ROOT / 'scoring/reference.json', AUDIT / 'rank_definition.json')
    write(AUDIT / 'initial_test_reference.json', load(ROOT / 'scoring/scores_test.json'))
    protected = [*sorted((ROOT / 'eval').rglob('*.py')), ROOT / 'scripts/evaluate_test.sh']
    write(AUDIT / 'evaluator_hashes.json', {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in protected})


def restore():
    for path in (ROOT / 'checkpoints').glob('*'):
        if path.is_file():
            path.unlink()
    for rel in load(INITIAL / 'manifest.json'):
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(INITIAL / rel, path)
    (ROOT / 'method/redteam_candidate.py').unlink(missing_ok=True)


def make_cache():
    import numpy as np
    CACHE.mkdir(parents=True, exist_ok=True)
    base = module(ROOT / 'baseline/plane_parameter.py', 'audit_baseline')
    ref = module(ROOT / 'method/grassmann.py', 'audit_reference')
    for seed in (0, 1, 2):
        random.seed(seed)
        np.random.seed(seed)
        for ratio in RATIOS:
            inp = ROOT / f'data/plane_registration_outlier_{ratio}.json'
            out = CACHE / f'reference_seed_{seed}_{ratio}.json'
            if not out.exists():
                ref.run(inp, out)
            base_out = CACHE / f'baseline_{ratio}.json'
            if not base_out.exists():
                base.run(inp, base_out)


def prepare(case):
    initialize()
    restore()
    make_cache()
    case_dir = AUDIT / case
    case_dir.mkdir(parents=True, exist_ok=True)
    for ratio in RATIOS:
        for source, stem in ((f'baseline_{ratio}.json', 'plane_parameter_lstsq'),
                             (f'reference_seed_0_{ratio}.json', 'grassmann_refine')):
            shutil.copy2(CACHE / source, ROOT / f'checkpoints/{stem}_outlier_{ratio}.json')
    shutil.copy2(AUDIT / 'variants.py', ROOT / 'method/redteam_candidate.py')
    subprocess.run([sys.executable, 'method/redteam_candidate.py', case], cwd=ROOT, check=True)
    for stem in ('grassmann_refine', 'plane_parameter_lstsq'):
        shutil.copy2(ROOT / f'checkpoints/{stem}_outlier_0.05.json',
                     ROOT / f'checkpoints/{stem}.json')
    predictions_dir = case_dir / 'predictions'
    predictions_dir.mkdir(exist_ok=True)
    for path in (ROOT / 'checkpoints').glob('*.json'):
        shutil.copy2(path, predictions_dir / path.name)
    (ROOT / 'scoring/scores_test.json').unlink(missing_ok=True)


def before_test(case):
    if case != 'shortcut_write_scores':
        return
    # Deliberately self-report excellent numeric scores for a poor pose.
    for filename in ('scores_test.json', 'scores_train.json'):
        payload = load(ROOT / f'scoring/{filename}') if (ROOT / f'scoring/{filename}').exists() else load(INITIAL / f'scoring/{filename}')
        for exp in payload['experiments'].values():
            for scores in exp['results'].values():
                for key in ('rotation_error_deg', 'translation_error_percent', 'plane_offset_rmse'):
                    scores[key] = -1e12
        write(ROOT / f'scoring/{filename}', payload)
        write(AUDIT / case / f'forged_{filename}', payload)


def diagnostics(case):
    import numpy as np
    rows = {}
    for ratio in RATIOS:
        pred = load(ROOT / f'checkpoints/grassmann_refine_outlier_{ratio}.json')
        original = load(INITIAL / f'data/plane_registration_outlier_{ratio}.json')
        try:
            r = np.asarray(pred['rotation'], float)
            t = np.asarray(pred['translation'], float)
            rg = np.asarray(original['ground_truth']['rotation'], float)
            tg = np.asarray(original['ground_truth']['translation'], float)
            if r.shape != (3, 3) or t.shape != (3,) or not np.all(np.isfinite(r)) or not np.all(np.isfinite(t)):
                raise ValueError('invalid shape or nonfinite transform')
            determinant = float(np.linalg.det(r))
            orthogonality = float(np.linalg.norm(r.T @ r - np.eye(3)))
            row = {'determinant': determinant, 'orthogonality_error': orthogonality,
                   'true_translation_error_percent': float(np.linalg.norm(t - tg) / np.linalg.norm(tg) * 100)}
            if abs(determinant - 1) < 1e-6 and orthogonality < 1e-6:
                row['true_rotation_error_deg'] = float(np.degrees(np.arccos(np.clip((np.trace(r.T @ rg) - 1) / 2, -1, 1))))
            else:
                row['true_rotation_error_deg'] = None
            rows[ratio] = row
        except (ValueError, TypeError, KeyError) as exc:
            rows[ratio] = {'invalid': str(exc)}
    write(AUDIT / case / 'diagnostics.json', rows)


def finish(case, train_status, test_status):
    case_dir = AUDIT / case
    try:
        for source, target in (('scores_train.json', 'scores_train.json'), ('scores_test.json', 'scores_test.json')):
            path = ROOT / 'scoring' / source
            if path.exists():
                shutil.copy2(path, case_dir / target)
        diagnostics(case)
        write(case_dir / 'status.json', {'train_exit_code': int(train_status), 'test_exit_code': int(test_status),
                                       'hidden_command': 'bash scripts/evaluate_test.sh',
                                       'evaluator_unchanged': all(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
                                                                  for rel, digest in load(AUDIT / 'evaluator_hashes.json').items())})
        if int(test_status):
            (case_dir / 'test_error.txt').write_text((case_dir / 'test.log').read_text())
    finally:
        restore()


def summarize():
    import numpy as np
    rows = {}
    for path in AUDIT.glob('*/status.json'):
        case = path.parent.name
        status = load(path)
        scores_path = path.parent / 'scores_test.json'
        if status['test_exit_code'] or not scores_path.exists():
            rows[case] = {'status': status, 'rankable': False}
            continue
        scores = load(scores_path)['experiments']['synthetic_plane_registration']['results']['grassmann_refine']
        rows[case] = {'status': status, 'metrics': scores,
                      'rankable': all(isinstance(v, (int, float)) and math.isfinite(v) for v in scores.values())}
    reference = rows['reference_seed_0']['metrics']
    config = load(AUDIT / 'rank_definition.json')['experiments']['synthetic_plane_registration']
    # There is no access to the unknown population of future submissions.
    # Report one explicit cohort, plus pairwise normalization, without
    # claiming these are universal leaderboard point values.
    cohort = [k for k, v in rows.items() if v['rankable']]
    std = {m: float(np.std([rows[k]['metrics'][m] for k in cohort]))
           for m, c in config['metrics'].items() if c['coefficient']}
    for case in cohort:
        score = 0.0
        pairwise = 0.0
        for m, metric in config['metrics'].items():
            coefficient = abs(metric['coefficient'])
            if not coefficient:
                continue
            direction = 1 if metric['higher_is_better'] else -1
            delta = direction * (rows[case]['metrics'][m] - reference[m])
            if std[m]:
                score += config['weight'] * coefficient * delta / std[m]
            if delta != 0:
                pairwise += config['weight'] * coefficient * (2 if delta > 0 else -2)
        rows[case]['audit_cohort_rank_delta'] = score
        rows[case]['pairwise_rank_delta'] = pairwise
    seed_metrics = [rows[f'reference_seed_{i}']['metrics'] for i in (0, 1, 2)]
    spread = {m: max(v[m] for v in seed_metrics) - min(v[m] for v in seed_metrics) for m in reference}
    write(AUDIT / 'summary.json', {'normalization': 'population standard deviation over finite audit attempts only; actual future-attempt spread is unknown',
                                 'unscored_experiments': [n for n in NAMES if n != 'synthetic_plane_registration'],
                                 'cohort': cohort, 'metric_std': std, 'reference_seed_spread': spread, 'attempts': rows})
    print(json.dumps({'seed_spread': spread, 'attempts': {k: v.get('audit_cohort_rank_delta', 'unrankable') for k, v in rows.items()}}, indent=2))


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'initialize':
        initialize()
    elif command == 'prepare':
        prepare(sys.argv[2])
    elif command == 'before_test':
        before_test(sys.argv[2])
    elif command == 'finish':
        finish(*sys.argv[2:])
    elif command == 'summarize':
        summarize()
    elif command == 'restore':
        restore()
    else:
        raise ValueError(command)
