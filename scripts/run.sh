#!/bin/bash
# Job script: reproduce the reference end to end (every registered solver on
# the visible and hidden instances) and validate the workspace.
#
# The hardening attempts reported in HARDENING.md can be re-run with
# `bash redteam/hardening/run.sh` (resumable; ~1 h on one CPU).
set -euo pipefail
cd /home/user
bash scripts/reproduce.sh
python3 validate.py --compare
