"""Helpers for the titlecase verifier. This module registers no criteria."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

HIDDEN_DATASET = Path("/tests/data/hidden.jsonl")
BUILD_TIMEOUT_SEC = 120
RUN_TIMEOUT_SEC = 60
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


def load_hidden_cases() -> list[dict[str, str]]:
    records = []
    with HIDDEN_DATASET.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"hidden dataset line {line_number} is not an object")
            text = record.get("input")
            expected = record.get("expected")
            if not isinstance(text, str) or not isinstance(expected, str):
                raise ValueError(f"hidden dataset line {line_number} is missing strings")
            records.append({"input": text, "expected": expected})
    if not records:
        raise ValueError("hidden dataset is empty")
    return records


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
    cases = load_hidden_cases()
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

    payload = "\n".join(case["input"] for case in cases) + "\n"
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
        for index, case in enumerate(cases)
        if index < len(lines) and lines[index] == case["expected"]
    )
    return matches / len(cases)
