#!/bin/bash
# Writes /logs/verifier/reward.json through Reward Kit.
set -uo pipefail

# The submitted program runs as `nobody` and must not be able to read answers.
chmod -R go-rwx /tests

# With no proxy and -mod=mod, any third-party import fails the build, even if
# it is vendored. CGO_ENABLED=0 rules out cgo.
export CGO_ENABLED=0 GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
    rewardkit /tests/checks --workspace /workspace/repo --max-concurrent-programmatic 1
