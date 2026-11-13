import sys
from pathlib import Path
from rewardkit import criterion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import prepare

@criterion
def no_python(workspace: Path) -> bool:
    return prepare(workspace) and not any(
        path.name.endswith('.py') and (path.is_file() or path.is_symlink())
        for path in workspace.rglob('*')
    )
