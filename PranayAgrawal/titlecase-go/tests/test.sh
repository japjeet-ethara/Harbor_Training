#!/bin/bash
set -u

mkdir -p /logs/verifier

rewardkit /tests \
    --workspace /workspace/repo \
    --output /logs/verifier/reward.json

status=$?
if [ "$status" -ne 0 ] || [ ! -s /logs/verifier/reward.json ]; then
    echo "rewardkit did not produce a reward (exit $status); writing zero reward" >&2
    printf '{"reward": 0.0}\n' > /logs/verifier/reward.json
fi

exit 0
