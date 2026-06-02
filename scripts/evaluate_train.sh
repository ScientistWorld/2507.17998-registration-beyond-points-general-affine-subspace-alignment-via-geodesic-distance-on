#!/bin/bash
# Visible train-slice evaluator for the plane-registration gym.
#
# Mirrors scripts/evaluate.sh: it reads pre-generated prediction JSON files
# and writes a scores file, without importing or running code from method/.

set -e

cd /home/user
PYTHON_BIN="${PYTHON:-python3}"

mkdir -p scoring

if [ "${1:-}" = "--suite" ]; then
  shift
  if [ "$#" -gt 0 ] && [ -d "$1" ]; then
    "${PYTHON_BIN}" eval/train/evaluate.py \
      --suite \
      --checkpoints-dir "$1" \
      --output scoring/scores_train.json
  else
    "${PYTHON_BIN}" eval/train/evaluate.py \
      --suite \
      --output scoring/scores_train.json \
      "$@"
  fi
else
  if [ "$#" -gt 0 ] && [ -d "$1" ]; then
    "${PYTHON_BIN}" eval/train/evaluate.py \
      --checkpoints-dir "$1" \
      --output scoring/scores_train.json
  else
    "${PYTHON_BIN}" eval/train/evaluate.py \
      --output scoring/scores_train.json \
      "$@"
  fi
fi
