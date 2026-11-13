import sys
from pathlib import Path
from rewardkit import criterion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import prepare

@criterion
def build(workspace: Path) -> bool:
    return prepare(workspace)
