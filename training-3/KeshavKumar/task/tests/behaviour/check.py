"""Check 3 - behaviour (weight 4).

Builds the Go program (`go build -o <bin> .` in /workspace/repo), runs it as the
unprivileged user `nobody`, feeds it tests/data/inputs.txt (100,000 titles) on
stdin, and compares each output line byte for byte with tests/data/answers.txt.

score = (share - 0.5) / 0.5, and 0 when share <= 0.5, where share is the fraction
of lines that match. The first mismatches are written to
/logs/verifier/behaviour_mismatches.txt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common  # noqa: E402
from rewardkit import criterion  # noqa: E402


@criterion(description="share of exam lines that match the original Python exactly, above a 50% floor")
def exam_lines_match(workspace: Path) -> dict:
    share, why = common.behaviour_share(workspace)
    credit = common.behaviour_credit(share)
    return {"score": credit, "reasoning": f"{why}; share {share:.4%} -> credit {credit:.4f}"}
