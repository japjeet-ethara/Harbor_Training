"""Report-only hard-rule gate: no Python source files remain."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import no_python_ok

from rewardkit import criterion


@criterion(description="no .py files remain anywhere in the submission")
def no_python(workspace: Path) -> bool:
    return no_python_ok(workspace)
