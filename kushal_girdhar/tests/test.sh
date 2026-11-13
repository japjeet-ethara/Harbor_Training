#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
export LITELLM_LOCAL_MODEL_COST_MAP=True
python3 -m rewardkit /tests/checks --workspace /workspace/repo \
  --output /logs/verifier/reward.json --max-concurrent-programmatic 1
test -s /logs/verifier/reward.json
