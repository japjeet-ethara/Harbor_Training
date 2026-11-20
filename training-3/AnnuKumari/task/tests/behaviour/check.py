import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from go_build_util import evaluate_behaviour_raw


@criterion
def behaviour(workspace: Path) -> float:
    """Gated exact-match accuracy on the hidden 100,000-title exam."""
    acc = evaluate_behaviour_raw(workspace)
    if acc < 0.80:
        return round(acc ** 4, 6)
    return round(acc, 6)