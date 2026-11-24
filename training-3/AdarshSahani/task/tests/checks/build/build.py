"""Build submitted Go packages in an unprivileged, source-only staging tree."""

import sys
from pathlib import Path

from rewardkit.session import criterion

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_support import run_unprivileged_go_build


@criterion(description="go build ./... succeeds as an unprivileged user")
def build(workspace: Path) -> bool:
    return run_unprivileged_go_build(workspace)
