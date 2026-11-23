from pathlib import Path

from evaluator import evaluate
from rewardkit import criterion


@criterion
def behaviour(workspace: Path) -> float:
    return evaluate(workspace).behaviour
