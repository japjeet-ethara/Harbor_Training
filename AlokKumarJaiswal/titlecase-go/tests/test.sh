#!/bin/bash
rewardkit /tests/checks --workspace /workspace/repo --output /logs/verifier/reward.json
cat /logs/verifier/reward.json
printf '\n'
cat /logs/verifier/reward-details.json
printf '\n'
