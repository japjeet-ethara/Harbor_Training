"""Criterion: build. The logic is in port_check.py (shared, built and run once)."""

import sys
from pathlib import Path

from rewardkit import criterion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import port_check  # noqa: E402


@criterion(description="`go build ./...` passes, and the port gets at least half of the hidden titles right")
def build(workspace: Path) -> float:
    return 1.0 if port_check.builds() and port_check.is_real_port() else 0.0
