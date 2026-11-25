"""No-Python criterion, sharing the same compliance gate as every criterion.

The submission may not contain Python sources, an interpreter, an embedded
runtime, a native object/assembly escape hatch, a network oracle or a foreign
language runtime, and the unprivileged runner must not be able to start any
interpreter. It must also reproduce at least 98% of the hidden exam.
"""

import importlib.util
import pwd
import subprocess
from pathlib import Path

from rewardkit import criterion

_SPEC = importlib.util.spec_from_file_location(
    "tc_common", Path(__file__).with_name("_common.py")
)
_common = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_common)

BIN = Path("/tmp/tc_nopython_bin")
INTERPRETERS = (
    "/usr/bin/python3",
    "/usr/local/bin/python3",
    "/usr/bin/python",
)


def _runner_cannot_start_an_interpreter() -> bool:
    """Environment self-check: the unprivileged runner has no Python runtime."""
    pw = pwd.getpwnam("runner")
    env = {"PATH": "/usr/local/go/bin:/usr/bin:/bin", "HOME": pw.pw_dir}
    for candidate in INTERPRETERS:
        try:
            probe = subprocess.run(
                [candidate, "-c", "print(1)"],
                capture_output=True,
                user=pw.pw_uid,
                group=pw.pw_gid,
                env=env,
                timeout=10,
            )
        except Exception:
            continue  # missing or not executable by runner: good
        if probe.returncode == 0:
            return False
    return True


@criterion(
    description=(
        "no Python sources or interpreter, no embedded runtime, no exec/embed/"
        "cgo/network escape hatch, and matching behaviour"
    )
)
def no_python(workspace: Path) -> bool:
    if _common.audit(workspace):
        return False
    if not _runner_cannot_start_an_interpreter():
        return False
    result = _common.exam(workspace, BIN)
    if result is None:
        return False
    return result[3] >= _common.MIN_ACCURACY
