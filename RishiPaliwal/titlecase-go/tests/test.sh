#!/bin/bash

set -euo pipefail

exec uv tool run --from 'harbor-rewardkit==0.1.*' rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
