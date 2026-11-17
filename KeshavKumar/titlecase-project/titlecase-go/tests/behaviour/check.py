"""Check 3 - behaviour (weight 4).

Builds the Go program (`go build -o <bin> .` in /workspace/repo), feeds it
tests/data/hidden_inputs.txt on stdin, and scores the share of lines that are
byte-for-byte equal to tests/data/hidden_expected.txt (0.0 to 1.0).
Only the HIDDEN files are used. The first mismatches are written to
/logs/verifier/behaviour_mismatches.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="share of hidden lines that match the original Python exactly")
def hidden_lines_match(workspace: Path) -> dict:
    score, why = common.behaviour_score(workspace)
    return {"score": score, "reasoning": why}
