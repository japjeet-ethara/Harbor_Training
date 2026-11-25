#!/usr/bin/env bash
set -euo pipefail

cd /
umask 077
mkdir -p /logs/verifier
chmod 700 /logs/verifier
state_dir=$(mktemp -d)
trap 'rm -f -- "$state_dir/grade.json"; rmdir -- "$state_dir"' EXIT
export TITLECASE_GRADE="$state_dir/grade.json"
export LITELLM_LOCAL_MODEL_COST_MAP=True
/usr/local/bin/python /tests/grade.py --output "$TITLECASE_GRADE"
/usr/local/bin/rewardkit /tests --workspace /workspace/repo
