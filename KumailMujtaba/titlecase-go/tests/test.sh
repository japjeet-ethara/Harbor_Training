#!/bin/bash

# Dependencies are installed in tests/Dockerfile. A rewardkit failure leaves no
# reward.json on purpose: a broken verifier must not look like a score of 0.
rewardkit /tests --workspace /workspace/repo --output /logs/verifier/reward.json
