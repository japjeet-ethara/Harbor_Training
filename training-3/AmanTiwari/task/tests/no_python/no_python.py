"""no_python gate (report-only; weight 0 in reward.toml): no .py file left under the
workspace -> 1, else 0.

It no longer pays points on its own: behaviour is 0 unless this gate passes, so
deleting the Python files is necessary but no longer sufficient for any score.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared import no_python_ok  # noqa: E402

import rewardkit as rk  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="no .py files left anywhere under /workspace/repo")
def no_python_files(workspace: Path) -> bool:
    return no_python_ok(workspace)


rk.no_python_files()
