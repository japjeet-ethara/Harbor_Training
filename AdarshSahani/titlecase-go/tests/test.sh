#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json

if rewardkit /tests/checks \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json; then
  if [[ ! -s /logs/verifier/reward.json ]]; then
    printf '{"reward": 0}\n' > /logs/verifier/reward.json
  fi
else
  printf '{"reward": 0}\n' > /logs/verifier/reward.json
fi
