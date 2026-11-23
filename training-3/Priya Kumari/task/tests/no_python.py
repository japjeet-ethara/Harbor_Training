"""No Python files may remain, and the Go port must pass a correctness smoke test."""

import subprocess
from pathlib import Path

from rewardkit import criterion

SMOKE_INPUTS = (
    "mcclelland\n"
    "iTunes should be unmolested\n"
    "this is just an example.com\n"
    "end-to-end\n"
)

SMOKE_EXPECTED = (
    "McClelland\n"
    "iTunes Should Be Unmolested\n"
    "This Is Just an example.com\n"
    "End-to-End\n"
)


def _smoke_test_passes(workspace: Path) -> bool:
    try:
        build = subprocess.run(
            ["go", "build", "-o", "/tmp/smoke_test", "."],
            cwd=workspace,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if build.returncode != 0:
            return False
        run = subprocess.run(
            ["/tmp/smoke_test"],
            input=SMOKE_INPUTS.encode("utf-8"),
            capture_output=True,
            timeout=30,
            check=False,
        )
        if run.returncode != 0:
            return False
        actual = run.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
        return actual == SMOKE_EXPECTED
    except (OSError, subprocess.TimeoutExpired):
        return False


@criterion
def no_python(workspace: Path) -> bool:
    if not workspace.is_dir():
        return False
    if any(path.is_file() for path in workspace.rglob("*.py")):
        return False
    return _smoke_test_passes(workspace)
