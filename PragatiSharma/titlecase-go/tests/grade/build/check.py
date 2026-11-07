import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rewardkit import criterion

from support import go_build_all, log


@criterion
def build(workspace: Path) -> dict[str, object]:
    ok, detail = go_build_all(workspace)
    log(f"build: {detail}")
    return {"score": ok, "reasoning": detail}
