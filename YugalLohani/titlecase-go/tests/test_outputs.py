"""
This file is kept as documentation only.

The active verifier is:
  tests/test.sh      — calls `rewardkit /tests`
  tests/grader.py    — defines the three weighted criteria via RewardKit

Weights and expected rewards:
  build     weight=1 (binary: go build ./... passes)
  no_python weight=1 (binary: build passes AND no .py files)
  behaviour weight=4 (float:  fraction of hidden lines matching expected)

  nothing done  → reward = 0.000
  build only    → reward ≈ 0.167
  perfect       → reward = 1.000
"""
