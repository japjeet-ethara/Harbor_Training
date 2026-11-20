"""Check 3 (weight 4): share of HIDDEN titles the Go program gets exactly right.

Uses only tests/data/hidden_*.txt, which the agent never sees, so printing
the visible answer sheet scores (almost) nothing here.
"""

import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

DATA = Path(__file__).resolve().parent / "data"


def _lines(path: Path) -> list[str]:
    text = path.read_bytes().decode("utf-8")
    return text.split("\n")[:-1]  # every file ends with exactly one "\n"


@criterion(description="Go program output matches the original Python on the hidden titles")
def hidden_titles_match(workspace: Path) -> float:
    expected = _lines(DATA / "hidden_expected.txt")
    data = (DATA / "hidden_inputs.txt").read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp) / "titlecase"
        try:
            build = subprocess.run(
                ["go", "build", "-o", str(binary), "."],
                cwd=workspace, capture_output=True, timeout=300,
            )
            if build.returncode != 0:
                return 0.0
            run = subprocess.run(
                [str(binary)], input=data, cwd=workspace, capture_output=True, timeout=120
            )
        except Exception:
            return 0.0
    got = run.stdout.decode("utf-8", errors="replace").split("\n")
    correct = sum(1 for i, want in enumerate(expected) if i < len(got) and got[i] == want)
    return correct / len(expected)
