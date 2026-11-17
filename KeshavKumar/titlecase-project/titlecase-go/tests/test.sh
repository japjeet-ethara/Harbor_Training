#!/bin/bash
# Runs in the SEPARATE verifier container (image built from tests/Dockerfile).
# The agent's /workspace/repo is uploaded here as an artifact (see task.toml).
#
# Reward Kit is downloaded with uvx, so the verifier needs network access.
# It writes /logs/verifier/reward.json with one score per check plus "reward":
#   {"behaviour": ..., "build": ..., "no_python": ..., "reward": ...}

mkdir -p /logs/verifier

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.4' \
  rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
