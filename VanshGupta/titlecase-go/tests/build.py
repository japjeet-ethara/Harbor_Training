import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _go


@criterion
def build(workspace: Path) -> bool:
    return _go.build_all(workspace)
