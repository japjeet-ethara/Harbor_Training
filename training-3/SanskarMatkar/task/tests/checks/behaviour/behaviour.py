"""behaviour (weight 4): share of the 100,000 hidden titles (tests/data/
inputs.txt) whose output equals the frozen answer (tests/data/answers.txt)
byte for byte.

The answers come from the ORIGINAL python-titlecase WITHOUT the `regex`
package (kit/answers.py, run twice, 0 unstable inputs dropped).
The program runs in an empty chroot as nobody (see /tests/lib/grade.py), so it
can read neither the answers nor any interpreter. Forbidden imports -> 0.
"""
import sys
from pathlib import Path

import rewardkit as rk

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
import grade  # noqa: E402


@rk.criterion(description="Share of 100,000 hidden titles whose output matches Python (no regex) byte for byte")
def hidden_output_matches(workspace: Path) -> float:
    return grade.grade(workspace)["behaviour"]
