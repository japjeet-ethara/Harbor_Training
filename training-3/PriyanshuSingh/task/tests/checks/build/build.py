"""build: `go build ./...` passes AND the program gets real titles right.

Before Day 5 this check paid 1.0 for any program that compiled, so an empty
`func main() {}` earned 1/6 of the reward on its own. Now it pays the same
behaviour score as the behaviour check, and only when the build passes.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, "/tests/lib")
import grading  # noqa: E402


@rk.criterion(description="go build ./... passes and the program titlecases correctly")
def go_build(workspace: Path) -> float:
    if not grading.go_build_all(workspace):
        return 0.0
    return grading.behaviour_score(workspace)
