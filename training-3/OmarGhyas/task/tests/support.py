"""Helpers for the titlecase verifier. This module registers no criteria."""

from __future__ import annotations

import subprocess
from pathlib import Path

INPUTS_FILE = Path("/tests/data/inputs.txt")
ANSWERS_FILE = Path("/tests/data/answers.txt")
BUILD_TIMEOUT_SEC = 120
RUN_TIMEOUT_SEC = 120
PROGRAM_USER = "nobody"


def go_build_succeeds(workspace: Path) -> bool:
    """Return whether `go build ./...` exits 0 in the workspace."""
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=workspace,
            capture_output=True,
            timeout=BUILD_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def python_files_absent(workspace: Path) -> bool:
    return not any(path.suffix == ".py" for path in workspace.rglob("*") if path.is_file())


def load_hidden_cases() -> tuple[list[str], list[str]]:
    with INPUTS_FILE.open(encoding="utf-8") as f_in, ANSWERS_FILE.open(encoding="utf-8") as f_ans:
        inputs = f_in.read().split("\n")[:-1]
        expected = f_ans.read().split("\n")[:-1]
    if len(inputs) != len(expected):
        raise ValueError(f"mismatched line counts: inputs={len(inputs)}, expected={len(expected)}")
    if not inputs:
        raise ValueError("hidden dataset is empty")
    return inputs, expected


def output_lines(stdout: bytes) -> list[str] | None:
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if text.endswith("\n"):
        text = text[:-1]
    if text == "":
        return []
    return text.split("\n")


def behaviour_score(workspace: Path) -> float:
    """Build the workspace program and return the fraction of exact hidden matches."""
    if not go_build_succeeds(workspace) or not python_files_absent(workspace):
        return 0.0
    inputs, expected = load_hidden_cases()
    binary = Path("/var/grader/titlecase")
    binary.unlink(missing_ok=True)
    try:
        built = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=workspace,
            capture_output=True,
            timeout=BUILD_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0
    if built.returncode != 0 or not binary.is_file():
        return 0.0
    binary.chmod(0o755)

    payload = "\n".join(inputs) + "\n"
    try:
        ran = subprocess.run(
            [str(binary)],
            input=payload.encode("utf-8"),
            capture_output=True,
            timeout=RUN_TIMEOUT_SEC,
            check=False,
            user=PROGRAM_USER,
            cwd="/var/grader",
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0.0

    lines = output_lines(ran.stdout)
    if lines is None:
        return 0.0
    matches = sum(
        1
        for index, want in enumerate(expected)
        if index < len(lines) and lines[index] == want
    )
    rate = matches / len(expected)
    if rate < 0.90:
        return 0.0
    return (rate - 0.90) / 0.10
