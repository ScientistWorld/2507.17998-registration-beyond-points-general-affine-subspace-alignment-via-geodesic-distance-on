#!/bin/bash
# A standalone attempt: install outputs, run visible feedback, then the exact
# no-argument hidden-test entry point in a separate process.
set -eu
cd /home/user
case_name="$1"
python3 redteam/harness.py prepare "$case_name"
set +e
bash scripts/evaluate_train.sh --suite > "redteam/$case_name/train.log" 2>&1
train_status=$?
python3 redteam/harness.py before_test "$case_name"
bash scripts/evaluate_test.sh > "redteam/$case_name/test.log" 2>&1
test_status=$?
set -e
python3 redteam/harness.py finish "$case_name" "$train_status" "$test_status"
