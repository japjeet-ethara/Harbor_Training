#!/bin/sh
mkdir -p /logs/verifier
# The submitted program runs unprivileged; it must not touch the reward files.
chmod 700 /logs/verifier
exec rewardkit /tests/grade \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json \
    --max-concurrent-programmatic 1
