#!/bin/bash
# Verifier entry point. Runs in the separate verifier container (tests/Dockerfile)
# after the agent has finished; the agent's /workspace/repo arrives as an artifact.
# Reward Kit is installed in the image, so no network is needed here.
set -u

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt

GOCACHE="$(mktemp -d /tmp/grade-gocache.XXXXXX)"
export GOCACHE GOTOOLCHAIN=local GOPROXY=off GOFLAGS= GOENV=off

rewardkit /tests/checks --workspace /workspace/repo --output /logs/verifier/reward.json
status=$?

if [ ! -s /logs/verifier/reward.json ]; then
  echo "rewardkit exited with status $status before writing a reward"
  echo '{"reward": 0, "build": 0, "no_python": 0, "behaviour": 0}' > /logs/verifier/reward.json
fi
cat /logs/verifier/reward.json
exit 0
