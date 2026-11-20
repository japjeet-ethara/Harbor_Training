#!/bin/bash
# Runs in the separate verifier container. /workspace/repo is the agent's finished work;
# /tests (this folder, including the hidden answers) exists only here.
# Reward Kit is downloaded with uvx, so this container needs network access.
set -u

export TESTS_DIR="${TESTS_DIR:-/tests}"
REPO_DIR="${REPO_DIR:-/workspace/repo}"
OUT="${REWARD_OUT:-/logs/verifier/reward.json}"
mkdir -p "$(dirname "$OUT")"

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.4' \
    rewardkit "$TESTS_DIR/checks" --workspace "$REPO_DIR" --output "$OUT"
