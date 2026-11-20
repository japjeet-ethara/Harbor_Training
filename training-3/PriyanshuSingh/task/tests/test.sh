#!/bin/bash
# Writes /logs/verifier/reward.json through Reward Kit.
set -uo pipefail

# The submitted program runs as `nobody` and must not be able to read answers.
chmod -R go-rwx /tests

# With no proxy and -mod=mod, any third-party import fails the build, even if
# it is vendored. CGO_ENABLED=0 rules out cgo.
export CGO_ENABLED=0 GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local

# Only Reward Kit may write the reward. Start from an empty slate so a file the
# agent or the graded program left behind is never read as the score.
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt

uvx --python '>=3.12,<3.14' --from 'harbor-rewardkit==0.2.*' \
    rewardkit /tests/checks --workspace /workspace/repo --max-concurrent-programmatic 1
status=$?

# tests/lib/grading.py already kills everything the graded program started
# after each run. Do it once more here, so no process owned by nobody can
# overwrite the reward after this script ends. Reward Kit writes reward.json
# only, so a reward.txt here can only come from the graded program.
setpriv --reuid=65534 --regid=65534 --clear-groups /bin/kill -9 -1 2>/dev/null
rm -f /logs/verifier/reward.txt
exit $status
