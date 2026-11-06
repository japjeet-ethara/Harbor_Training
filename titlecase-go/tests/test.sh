#!/bin/bash
# Runs Reward Kit over /tests (build.py, no_python.py, behaviour.py + reward.toml)
# against the agent's work in /workspace/repo and writes /logs/verifier/reward.json.
set -uo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json

/opt/rk/bin/python -m rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json

# Reward Kit must have produced a score; otherwise the verifier errors (no silent 0).
test -s /logs/verifier/reward.json
