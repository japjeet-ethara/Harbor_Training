#!/bin/bash
# Verifier entry point. Harbor copies the agent's /workspace/repo into this
# separate container (see [[artifacts]] in task.toml), then runs this script.
# Reward Kit runs build.py, no_python.py and behaviour.py, combines them with
# the weights in reward.toml, and writes /logs/verifier/reward.json.
set -uo pipefail

mkdir -p /logs/verifier /workspace/repo
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
