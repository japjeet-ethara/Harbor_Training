#!/bin/sh
set -eu
mkdir -p /logs/verifier
chmod 700 /tests /logs/verifier
cd /tests
python -I -m rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json --max-concurrent-programmatic 1
