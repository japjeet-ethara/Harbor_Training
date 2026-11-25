from pathlib import Path

from evaluator import evaluate
from rewardkit import criterion


@criterion
def no_python(workspace: Path) -> bool:
    return evaluate(workspace).no_python
