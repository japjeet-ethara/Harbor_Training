#!/bin/bash
exec uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
  rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
