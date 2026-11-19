#!/bin/bash
# Grade the repository with Reward Kit. Dependencies are installed in the image.
set -uo pipefail

mkdir -p /logs/verifier

# One build at a time. Parallel `go build` invocations share a module directory.
python3 -m rewardkit /tests \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
status=$?

if [[ ! -s /logs/verifier/reward.json ]]; then
  exit "$status"
fi

exit "$status"
