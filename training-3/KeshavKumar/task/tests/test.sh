#!/bin/bash
# Runs in the SEPARATE verifier container (image built from tests/Dockerfile),
# with NO network. The agent's /workspace/repo is uploaded here as an artifact
# (see task.toml). Reward Kit is already installed in the image.
#
# The agent's program is run as `nobody` (tests/common.py). Make sure nobody
# cannot read the answer key or touch the logs, even if Harbor re-uploaded
# /tests with looser permissions.
#
# Writes /logs/verifier/reward.json:
#   {"behaviour": ..., "build": ..., "no_python": ..., "reward": ...}
set -u
mkdir -p /logs/verifier
chmod -R go-rwx /tests
chmod 700 /logs/verifier 2>/dev/null || true

/root/.local/bin/rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
