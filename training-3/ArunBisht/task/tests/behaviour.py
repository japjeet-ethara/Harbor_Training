"""behaviour: exact-output score, gated below the minimum oracle threshold."""

from pathlib import Path

from rewardkit import criterion
from score_utils import MIN_BEHAVIOUR_SCORE, score_behaviour

@criterion
def behaviour(workspace: Path) -> float:
    score = score_behaviour(workspace)
    return score if score >= MIN_BEHAVIOUR_SCORE else 0.0
