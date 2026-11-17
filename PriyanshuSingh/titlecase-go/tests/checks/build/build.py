"""build: `go build ./...` passes in the repository."""
import rewardkit as rk

rk.command_succeeds("go build ./...", timeout=300, name="go_build")
