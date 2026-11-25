#!/bin/bash
set -eo pipefail

mkdir -p /logs/verifier

# Run RewardKit against the verifier tests and workspace.
PYTHONPATH=/tests uvx --from 'harbor-rewardkit==0.2.*' rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
