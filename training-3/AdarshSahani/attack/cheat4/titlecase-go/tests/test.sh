#!/bin/bash
# Verifier entry point. Reward Kit runs build.py, no_python.py and behaviour.py,
# combines them with tests/reward.toml and writes /logs/verifier/reward.json.
set -uo pipefail
mkdir -p /logs/verifier /workspace/repo   # a deleted repo must score 0, not crash the verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json
if command -v rewardkit >/dev/null 2>&1; then RK=(rewardkit); else
  RK=(uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.4' rewardkit); fi
"${RK[@]}" /tests --workspace /workspace/repo --output /logs/verifier/reward.json
