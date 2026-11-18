#!/bin/sh
exec python3 -m rewardkit /tests \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json
