from pathlib import Path
from rewardkit import criterion
from grader import evaluate


@criterion
def build_go_standard_library_main(workspace: Path) -> float:
    """A root Go executable builds; its production dependencies use only stdlib."""
    return evaluate(workspace)["build"]
