from pathlib import Path
from rewardkit import criterion
from grader import evaluate


@criterion
def remove_python_only_after_build(workspace: Path) -> float:
    """No .py files remain anywhere in the submitted repo, and the build passes."""
    return evaluate(workspace)["no_python"]
