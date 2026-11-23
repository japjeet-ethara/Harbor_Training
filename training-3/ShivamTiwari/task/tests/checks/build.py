"""Build criterion, gated by the shared compliance audit.

`go build ./...` must succeed, the submission must clear the structural rules
and the built binary must reproduce at least 98% of the hidden exam. A stub
that merely compiles, a lookup wrapper, or a correct port that also ships a
banned file/import earns nothing.
"""

import importlib.util
import subprocess
from pathlib import Path

from rewardkit import criterion

_SPEC = importlib.util.spec_from_file_location(
    "tc_common", Path(__file__).with_name("_common.py")
)
_common = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_common)

BIN = Path("/tmp/tc_build_bin")


@criterion(
    description=(
        "go build ./... succeeds, the submission obeys every structural rule, "
        "and the binary matches the hidden exam"
    )
)
def build(workspace: Path) -> bool:
    if _common.audit(workspace):
        return False
    compiled = subprocess.run(
        [_common.GO, "build", "./..."],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=300,
        env=_common.BUILD_ENV,
    )
    if compiled.returncode != 0:
        return False
    result = _common.exam(workspace, BIN)
    if result is None:
        return False
    return result[3] >= _common.MIN_ACCURACY
