#!/bin/bash
# Runs the three checks with Reward Kit, one at a time, which writes /logs/verifier/reward.json.
mkdir -p /logs/verifier
rewardkit /tests --workspace /workspace/repo --max-concurrent-programmatic 1
