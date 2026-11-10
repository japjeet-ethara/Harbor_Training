"""Check C: exact line-by-line behaviour on the hidden dataset."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    RUN_TIMEOUT_SEC,
    compare_lines,
    describe_build,
    describe_line,
    go_build_binary,
    go_env,
    tail,
)
from rewardkit.session import criterion  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HIDDEN_INPUTS = DATA_DIR / "hidden_inputs.txt"
HIDDEN_EXPECTED = DATA_DIR / "hidden_expected.txt"


@criterion(description="Check the Go program against hidden inputs byte for byte")
def behaviour(workspace: Path) -> dict:
    if not workspace.is_dir():
        return {"score": 0.0, "reasoning": f"workspace is missing: {workspace}"}

    try:
        hidden_inputs = HIDDEN_INPUTS.read_bytes()
        hidden_expected = HIDDEN_EXPECTED.read_bytes()
    except OSError as exc:
        return {"score": 0.0, "reasoning": f"hidden dataset unavailable: {exc}"}

    with tempfile.TemporaryDirectory(prefix="titlecase-verify-") as tmp:
        binary = Path(tmp) / "titlecase-go"
        try:
            build_proc = go_build_binary(workspace, binary)
        except Exception as exc:  # noqa: BLE001 - explicit failure reporting
            return {"score": 0.0, "reasoning": f"could not build the program: {exc}"}

        if build_proc.returncode != 0:
            return {
                "score": 0.0,
                "reasoning": f"could not build the program; {describe_build(build_proc)}",
            }

        try:
            proc = subprocess.run(
                [str(binary)],
                cwd=str(workspace),
                env=go_env(),
                input=hidden_inputs,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=RUN_TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired:
            return {
                "score": 0.0,
                "reasoning": f"program timed out after {RUN_TIMEOUT_SEC} seconds",
            }
        except Exception as exc:  # noqa: BLE001 - explicit failure reporting
            return {"score": 0.0, "reasoning": f"could not run the program: {exc}"}

        if proc.returncode != 0:
            stderr = tail(proc.stderr.decode("utf-8", errors="replace"))
            suffix = f"; stderr: {stderr}" if stderr else ""
            return {
                "score": 0.0,
                "reasoning": f"program exited with status {proc.returncode}{suffix}",
            }

        correct, total, first_bad, expected_lines, actual_lines = compare_lines(
            hidden_expected, proc.stdout
        )
        incorrect = total - correct
        if total == 0:
            return {"score": 0.0, "reasoning": "hidden dataset produced zero expected lines"}

        reasoning = (
            f"{correct} correct, {incorrect} incorrect, {total} total "
            f"(expected {len(expected_lines)} lines, got {len(actual_lines)} lines)"
        )
        if first_bad is not None:
            reasoning += "; " + describe_line(first_bad, expected_lines, actual_lines)
        return {"score": correct / total, "reasoning": reasoning}
