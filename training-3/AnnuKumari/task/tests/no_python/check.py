import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from go_build_util import evaluate_behaviour_raw, go_build, workspace_is_clean_go


@criterion
def no_python(workspace: Path) -> bool:
    """No Python files/signatures remain, stdlib-only Go builds, and behaviour >= 50%."""
    if not workspace_is_clean_go(workspace):
        return False
    if not go_build(workspace, ["build", "./..."]):
        return False
    return evaluate_behaviour_raw(workspace) >= 0.50