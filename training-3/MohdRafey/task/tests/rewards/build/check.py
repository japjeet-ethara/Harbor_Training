"""build: 1 if `go build ./...` passes in the repo, else 0."""

from rewardkit import criteria

criteria.command_succeeds("go build ./...", timeout=300, name="go_build")
