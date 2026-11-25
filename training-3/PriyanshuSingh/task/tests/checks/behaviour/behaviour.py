"""behaviour: share of hidden titles whose output matches exactly.

Scored by tests/lib/grading.py: 0 at or below a 50 % match, then rising in a
straight line to 1.0 at a perfect match.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, "/tests/lib")
import grading  # noqa: E402


@rk.criterion(description="Share of hidden titles matching the original output")
def hidden_titles_match(workspace: Path) -> float:
    return grading.behaviour_score(workspace)
