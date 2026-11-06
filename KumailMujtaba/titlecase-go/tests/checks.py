"""Reward Kit criteria for titlecase-go. Weights: build 1, no_python 1, behaviour 4.

An exception in a criterion aborts the whole run, so anything the agent's code
can cause (a failed build, a crash, a hang) has to score 0 here instead.
"""

import os
import subprocess
from functools import cache
from pathlib import Path

import rewardkit as rk
from rewardkit import criterion

DATA_DIR = Path(__file__).parent / "data"
# Outside the workspace, so building does not change what no_python sees.
BINARY = "/tmp/titlecase-go-under-test"
BUILD_TIMEOUT_SEC = 300
RUN_TIMEOUT_SEC = 120


def go_build(workspace, *args):
    try:
        result = subprocess.run(
            ["go", "build", *args],
            cwd=workspace,
            capture_output=True,
            timeout=BUILD_TIMEOUT_SEC,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


@cache
def builds(workspace):
    return go_build(workspace, "./...")


def has_python_file(workspace):
    return any(
        name.endswith(".py")
        for _, _, names in os.walk(workspace)
        for name in names
    )


def split_lines(data):
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


@criterion(description="go build ./... exits 0")
def build(workspace: Path) -> bool:
    return builds(workspace)


@criterion(description="no .py files remain and the build passes")
def no_python(workspace: Path) -> bool:
    return builds(workspace) and not has_python_file(workspace)


@criterion(description="share of hidden lines matching the original titlecase()")
def behaviour(workspace: Path) -> dict:
    if not go_build(workspace, "-o", BINARY, "."):
        return {"score": 0.0, "reasoning": "go build -o failed"}

    # /tests is root-only and this runs as nobody, so the program can read the
    # titles from stdin but cannot open the answers in /tests/data.
    try:
        with open(DATA_DIR / "hidden_inputs.txt", "rb") as stdin:
            result = subprocess.run(
                [BINARY],
                stdin=stdin,
                capture_output=True,
                timeout=RUN_TIMEOUT_SEC,
                cwd="/tmp",
                env={},
                user="nobody",
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"score": 0.0, "reasoning": f"could not run the program: {error}"}

    expected = split_lines((DATA_DIR / "hidden_expected.txt").read_bytes())
    actual = split_lines(result.stdout)
    matches = sum(a == e for a, e in zip(actual, expected))
    # Extra output lines count against the score, as missing ones do.
    total = max(len(expected), len(actual))
    return {
        "score": matches / total,
        "reasoning": f"{matches} of {total} lines match, exit code {result.returncode}",
    }


rk.build(weight=1.0)
rk.no_python(weight=1.0)
rk.behaviour(weight=4.0)
