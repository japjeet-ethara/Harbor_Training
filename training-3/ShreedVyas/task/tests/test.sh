#!/bin/sh
set -eu

exec rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
