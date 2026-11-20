import sys
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _grade  # noqa: E402


@criterion(description="share of exam titles cased exactly like the Python original (run as nobody)")
def matches_python(workspace: Path) -> float:
    return _grade.behaviour_score(workspace)


rk.matches_python()
