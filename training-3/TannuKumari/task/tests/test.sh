#!/bin/bash
# Reward Kit checks (weighted mean): build, no_python, behaviour.
# Hidden inputs stay in this verifier image and are not mounted for the agent.
set -euo pipefail

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
  rewardkit /tests/checks --workspace /workspace/repo \
  --max-concurrent-programmatic 1
