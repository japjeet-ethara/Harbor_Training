"""Build-time self-test for tests/Dockerfile: `nobody` must not run any interpreter.

Not a criterion; rewardkit only loads functions marked @criterion.
"""
import subprocess
import sys

INTERPRETERS = (
    "/usr/local/bin/python3", "/usr/local/bin/python3.12", "/usr/bin/perl",
    "/usr/bin/mawk", "/bin/sh", "/bin/bash", "/bin/dash", "/usr/local/go/bin/go",
)


def nobody_can_run(path: str) -> bool:
    try:
        result = subprocess.run(
            [path, "--version"], user="nobody", group="nogroup", extra_groups=[],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except PermissionError:
        return False
    return result.returncode == 0


if __name__ == "__main__":
    # Positive control: root (this process) can still run Python.
    assert subprocess.run([sys.executable, "-I", "-c", "import re"]).returncode == 0
    open_paths = [p for p in INTERPRETERS if nobody_can_run(p)]
    if open_paths:
        sys.exit(f"nobody can still run: {open_paths}")
    print(f"locked for nobody: {len(INTERPRETERS)} interpreters")
