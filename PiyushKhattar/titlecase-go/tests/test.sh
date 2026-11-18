#!/bin/sh
set -eu

mkdir -p /logs/verifier

rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
