"""build: go build ./... in /workspace/repo scores 1, otherwise 0."""

import rewardkit as rk

rk.command_succeeds("go build ./...", timeout=180)
