"""Criterion: behaviour. The logic is in port_check.py (shared, built and run once)."""

import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import port_check  # noqa: E402


@criterion(description="share of the 100,000 hidden titles reproduced byte for byte (port runs alone in an empty jail)")
def behaviour(workspace: Path) -> float:
    return port_check.behaviour()
