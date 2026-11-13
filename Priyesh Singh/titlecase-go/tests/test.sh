#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
export PATH="/root/.local/bin:${PATH}"
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
