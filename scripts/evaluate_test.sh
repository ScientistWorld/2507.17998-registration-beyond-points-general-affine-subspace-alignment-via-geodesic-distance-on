#!/bin/bash
# Held-out test-slice evaluator for the plane-registration gym.
#
# Scores the same method set as scoring/scores_train.json when that file is
# present, using pre-generated prediction JSON files and no method imports.

set -e

cd /home/user
PYTHON_BIN="${PYTHON:-python3}"

mkdir -p scoring

if [ "${1:-}" = "--suite" ]; then
  shift
  if [ "$#" -gt 0 ] && [ -d "$1" ]; then
    "${PYTHON_BIN}" eval/test/evaluate.py \
      --suite \
      --checkpoints-dir "$1" \
      --output scoring/scores_test.json
  else
    "${PYTHON_BIN}" eval/test/evaluate.py \
      --suite \
      --output scoring/scores_test.json \
      "$@"
  fi
else
  if [ "$#" -gt 0 ] && [ -d "$1" ]; then
    "${PYTHON_BIN}" eval/test/evaluate.py \
      --checkpoints-dir "$1" \
      --output scoring/scores_test.json
  else
    "${PYTHON_BIN}" eval/test/evaluate.py \
      --output scoring/scores_test.json \
      "$@"
  fi
fi
