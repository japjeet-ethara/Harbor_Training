"""Score 1 when `go build ./...` succeeds in the submitted workspace."""

import rewardkit as rk

rk.command_succeeds("go build ./...", timeout=180)
