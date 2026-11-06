import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _go


@criterion
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    has_python = any(path.is_file() for path in workspace.rglob("*.py"))
    return not has_python and _go.build_all(workspace)
