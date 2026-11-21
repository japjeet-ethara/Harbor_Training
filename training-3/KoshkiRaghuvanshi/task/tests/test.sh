#!/bin/sh
exec /opt/rewardkit/bin/python3 -m rewardkit /tests \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json
