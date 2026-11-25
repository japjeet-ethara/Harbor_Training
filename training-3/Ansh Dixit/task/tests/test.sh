#!/bin/bash
# Verifier entry point. Runs inside the separate verifier container, where the
# agent's /workspace/repo has been copied in (see `artifacts` in task.toml).
# Reward Kit is baked into the verifier image, so no network is needed.
mkdir -p /logs/verifier
cd /tests
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
