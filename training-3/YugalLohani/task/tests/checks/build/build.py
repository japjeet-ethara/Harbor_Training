"""build (weight 1): `go build ./...` passes, standard library only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import grading  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="go build ./... passes and only the standard library is used")
def go_build_passes(workspace: Path) -> bool:
    try:
        return grading.build_ok(Path(workspace))
    except Exception as exc:  # never crash the verifier
        grading.log(f"[build] grader error: {exc!r}")
        return False
