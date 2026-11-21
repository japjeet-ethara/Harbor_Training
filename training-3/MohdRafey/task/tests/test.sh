#!/bin/bash

# Writes the reward to /logs/verifier/reward.json.
# One check at a time, because `go build ./...` can write into the repo.
rewardkit /tests/rewards \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
