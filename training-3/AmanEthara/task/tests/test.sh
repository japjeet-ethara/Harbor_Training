#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

if command -v rewardkit >/dev/null 2>&1; then
    rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
elif command -v uvx >/dev/null 2>&1; then
    uvx --from 'harbor-rewardkit==0.2.*' rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
else
    echo "ERROR: Neither rewardkit nor uvx found" >&2
    exit 1
fi
