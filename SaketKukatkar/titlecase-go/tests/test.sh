#!/bin/bash
# Verifier entry point. Reward Kit runs the three criteria in /tests against the
# agent's repository and writes /logs/verifier/reward.json.
set -uo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
    rewardkit --workspace /workspace/repo --output /logs/verifier/reward.json /tests
