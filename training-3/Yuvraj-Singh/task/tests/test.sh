#!/bin/bash
set -euo pipefail

export PATH="/root/.local/bin:${PATH}"

mkdir -p /logs/verifier
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
