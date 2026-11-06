#!/bin/sh
set -eu
mkdir -p /logs/verifier
exec python -m rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
