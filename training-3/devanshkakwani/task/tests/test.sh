#!/bin/sh
set -eu

exec python -m rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
