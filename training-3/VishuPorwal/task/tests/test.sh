#!/bin/bash

mkdir -p /logs/verifier

uv tool run --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
  rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
