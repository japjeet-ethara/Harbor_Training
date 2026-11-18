#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.4' rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
