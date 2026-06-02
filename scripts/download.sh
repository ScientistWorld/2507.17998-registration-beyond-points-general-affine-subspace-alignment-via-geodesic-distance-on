#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: 0 GB
#
# You do not need to run this script during reproduction. It exists for future
# portability and writes only workspace-local paths.

set -e

cd /home/user

mkdir -p data/downloads
echo "No external datasets or model weights are required."
