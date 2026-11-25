import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import criteria
import rewardkit as rk


@rk.criterion(description="go build ./... succeeds")
def build(workspace: Path) -> float:
    return criteria.build_check(workspace)
