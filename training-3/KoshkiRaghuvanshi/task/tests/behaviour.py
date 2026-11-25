import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rewardkit import criterion

from go_run import passes_behaviour


@criterion
def behaviour(workspace: Path) -> float:
    return 1.0 if passes_behaviour(workspace) else 0.0
