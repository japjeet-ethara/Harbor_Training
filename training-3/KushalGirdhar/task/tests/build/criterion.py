from pathlib import Path

from evaluator import evaluate
from rewardkit import criterion


@criterion
def build(workspace: Path) -> bool:
    return evaluate(workspace).build
