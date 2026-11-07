#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

python3 -m rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
