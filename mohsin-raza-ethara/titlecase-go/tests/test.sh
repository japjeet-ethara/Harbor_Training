#!/bin/bash
set -euo pipefail

# uvx downloads Reward Kit at runtime (network_mode = "public" in task.toml).
# It discovers the criteria in /tests (bundled by tests/Dockerfile), runs
# them against the agent's repository at /workspace/repo, and writes the
# reward to /logs/verifier/reward.json.
mkdir -p /logs/verifier

exec uvx --from 'harbor-rewardkit==0.2.*' rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
