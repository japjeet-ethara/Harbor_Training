"""Score 1.0 when the workspace builds and contains no Python files."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion
from support import go_build_succeeds, python_files_absent


@criterion
def no_python(workspace: Path) -> float:
    if not python_files_absent(workspace):
        return 0.0
    return 1.0 if go_build_succeeds(workspace) else 0.0
