#!/bin/bash
# Run every hardening attempt through the hidden test, then summarise.
# Resumable: finished attempts (results/<name>/status_<split>.json) are skipped.
set -uo pipefail
cd "$(dirname "$0")/../.."
python3 redteam/hardening/harness.py run
python3 redteam/hardening/harness.py summarize
