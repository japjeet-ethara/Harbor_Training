"""no_python (weight 1): no Python file by NAME or by CONTENT anywhere under
/workspace/repo, the build passes, AND behaviour >= GATE -> 1, else 0.

Content check: the original source renamed to .txt and //go:embed-ed still
counts as Python (Day 4 cheat 2). The gate stops "delete the .py files and
build an empty program" from earning anything (Day 4 cheat 3).
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
import grade  # noqa: E402


@rk.criterion(description="No Python (by name or content) remains, build passes, behaviour >= 0.5")
def no_python_and_builds(workspace: Path) -> bool:
    r = grade.grade(workspace)
    return r["no_python"] and r["built"] and grade.gated(r)
