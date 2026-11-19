#!/bin/bash

# Grade the agent workspace from the separate verifier image.
# Hidden fixtures are baked into this image under /tests/data.
set -euo pipefail

mkdir -p /logs/verifier

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
  rewardkit /tests/checks \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
