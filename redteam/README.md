# Scoring audit artifacts

See [REDTEAM.md](../REDTEAM.md) for the findings, quality checks, seed spread,
and one row per shortcut.

Submit `bash redteam/run_all.sh` as a CPU job to repeat all attempts. Each
attempt also has its own `run.sh`. Run these scripts in the original gym
container at `/home/user`; actual estimation and evaluation belong on compute
nodes, not the login node. NumPy and SciPy are the gym's existing dependencies.

`variants.py` contains candidate implementations and is copied temporarily
into `method/` by `harness.py`. The shared harness restores datasets, predictions,
and score files after each attempt. `run_case.sh` always invokes the original
hidden test with no arguments and records exit codes, hashes, predictions,
scores, and actual-pose diagnostics. Invalid attempts may have only a traceback
instead of a test score.

`summary.json` gives all measured vectors and an explicitly identified finite
audit-cohort normalization. The actual normalization across future submissions
is unknown. `rank_definition.json`, `initial_test_reference.json`, and
`evaluator_hashes.json` are auditor evidence, never candidate inputs. The
ignored `_initial/` and `_cache/` directories are rebuilt on demand and are
not required in a fresh checkout.
