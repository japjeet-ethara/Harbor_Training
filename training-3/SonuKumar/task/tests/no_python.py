import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import criteria
import rewardkit as rk


@rk.criterion(description="no Python files remain and the Go project builds")
def no_python(workspace: Path) -> float:
    return criteria.no_python_check(workspace)
