#!/bin/sh
mkdir -p /logs/verifier
exec rewardkit /tests/grade \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json \
    --max-concurrent-programmatic 1
