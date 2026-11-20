"""behaviour (weight 4): share of hidden lines whose output matches exactly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

import grading  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="share of hidden_inputs.txt lines matching hidden_expected.txt")
def hidden_lines_match(workspace: Path) -> float:
    try:
        matched, total, _changed = grading.hidden_results(Path(workspace))
        return matched / total if total else 0.0
    except Exception as exc:
        grading.log(f"[behaviour] grader error: {exc!r}")
        return 0.0
