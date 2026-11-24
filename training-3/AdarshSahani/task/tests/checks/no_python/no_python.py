"""Diagnostic: report whether any Python files remain in the workspace."""

from pathlib import Path

from rewardkit.session import criterion


@criterion(description="No .py files remain under the workspace")
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    try:
        return not any(
            path.is_file() and path.suffix == ".py"
            for path in workspace.rglob("*")
        )
    except OSError:
        return False
