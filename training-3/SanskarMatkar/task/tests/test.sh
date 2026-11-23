#!/bin/bash
# Verifier entry point. Runs in the separate verifier container after the agent
# stops; /workspace/repo is the agent's repository (copied in as an artifact).
# Writes /logs/verifier/reward.json with build, no_python, behaviour and reward.
set -uo pipefail

mkdir -p /logs/verifier
export GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=readonly CGO_ENABLED=0
export GOCACHE="${GOCACHE:-/tmp/go-build-cache}"

if command -v rewardkit >/dev/null 2>&1; then
  RK=(rewardkit)                                   # baked into tests/Dockerfile
else
  RK=(uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' rewardkit)
fi

"${RK[@]}" /tests/checks \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json
status=$?

cat /logs/verifier/reward.json 2>/dev/null || echo "reward.json missing (rewardkit exit $status)"
exit $status
