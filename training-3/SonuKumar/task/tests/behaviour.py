import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import criteria
import rewardkit as rk


@rk.criterion(description="hidden titlecase outputs match")
def behaviour(workspace: Path) -> float:
    return criteria.behaviour_check(workspace)
