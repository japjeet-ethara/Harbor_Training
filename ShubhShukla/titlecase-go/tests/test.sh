#!/bin/sh
set -eu
mkdir -p /logs/verifier
exec python3 -m rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
