#!/bin/bash
# Job script.  Reproduces the reference end to end (every registered solver on
# the visible and hidden instances), validates the workspace, then runs the
# hardening attempts through the hidden test.
set -uo pipefail
cd /home/user
# Job-only guard: a preempted+restarted job must not reproduce with a
# hardening attempt still installed as the only solver.
git checkout -- scripts/solvers data eval && git clean -fdq -- scripts/solvers data eval
python3 -c "import numpy, scipy; print('numpy', numpy.__version__, 'scipy', scipy.__version__)"
echo "== reproduce reference (scores.json, scores_train.json, scores_test.json)"
bash scripts/reproduce.sh
echo "reproduce exit: $?"
python3 validate.py --compare
echo "== hardening attempts"
bash redteam/hardening/run.sh
