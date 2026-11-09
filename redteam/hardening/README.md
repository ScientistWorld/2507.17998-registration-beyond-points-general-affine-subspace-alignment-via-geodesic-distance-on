# Hardening attempts (iteration 11)

Reported in [`HARDENING.md`](../../HARDENING.md).

- `variants.py` — better/weaker/ablation solvers and shortcut solvers, each a
  solver-contract CLI (`python3 variants.py <attempt> <problems> <predictions>`).
- `harness.py run` — installs each attempt as the only file in
  `scripts/solvers/`, runs the unchanged `bash scripts/evaluate_test.sh`
  (honest attempts add `--details`, which does not change scores; shortcuts
  run with no arguments), copies the scores, and restores every file the
  attempt could touch.  Resumable.  `harness.py summarize` writes
  `results/summary.{json,md}` (rank changes, paired bootstrap intervals,
  per-regime breakdowns, train vs test).
- `run.sh` — both steps; about one hour on one CPU.
