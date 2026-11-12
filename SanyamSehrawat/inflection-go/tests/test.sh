#!/bin/bash
# Verifier entry point. Reward Kit runs the three checks in /tests/checks against
# the agent's final repository and writes /logs/verifier/reward.json:
#
#   build      weight 1   `go build ./...` passes and the root package builds
#   no_python  weight 1   no .py file is left AND the build passes
#   behaviour  weight 4   share of hidden lines whose output matches exactly
#   reward                weighted mean of the three
#
# The checks run one at a time: two of them run `go build ./...` in the same
# folder, and running them together would make them write the same file at once.
set -uo pipefail

rewardkit /tests/checks \
  --workspace /workspace/repo \
  --output /logs/verifier/reward.json \
  --max-concurrent-programmatic 1
