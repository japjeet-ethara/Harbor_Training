"""
RewardKit criteria for titlecase-go.

Three checks, weighted-mean aggregation:
  build     (weight 1) — go build ./... passes in /workspace/repo
  no_python (weight 1) — build passes AND no .py files under /workspace/repo
  behaviour (weight 4) — fraction of hidden lines matching expected output

Expected rewards:
  nothing done  = (1×0 + 1×0 + 4×0.0) / 6 = 0.000
  build only    = (1×1 + 1×0 + 4×0.0) / 6 ≈ 0.167
  perfect       = (1×1 + 1×1 + 4×1.0) / 6 = 1.000
"""

import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

WORKDIR = Path("/workspace/repo")
HIDDEN_INPUTS = Path("/tests/data/hidden_inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/hidden_expected.txt")


def _build_ok() -> bool:
    """Return True if `go build ./...` exits 0 in WORKDIR."""
    result = subprocess.run(
        ["go", "build", "./..."],
        cwd=WORKDIR,
        capture_output=True,
    )
    return result.returncode == 0


@criterion(weight=1)
def build(workspace: Path) -> bool:
    """go build ./... must pass in /workspace/repo."""
    return _build_ok()


@criterion(weight=1)
def no_python(workspace: Path) -> bool:
    """Build passes AND no .py files remain anywhere under /workspace/repo."""
    if not _build_ok():
        return False
    return len(list(WORKDIR.rglob("*.py"))) == 0


@criterion(weight=4)
def behaviour(workspace: Path) -> float:
    """
    Fraction of hidden input lines whose Go output exactly matches
    the expected Python titlecase() output byte-for-byte.
    """
    if not _build_ok():
        return 0.0
    if not HIDDEN_INPUTS.exists() or not HIDDEN_EXPECTED.exists():
        return 0.0

    with tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp) / "titlecase"
        build_result = subprocess.run(
            ["go", "build", "-o", str(binary), "./..."],
            cwd=WORKDIR,
            capture_output=True,
        )
        if build_result.returncode != 0:
            return 0.0

        with open(HIDDEN_INPUTS, "rb") as inp:
            run_result = subprocess.run(
                [str(binary)],
                stdin=inp,
                capture_output=True,
            )

    actual = run_result.stdout.decode("utf-8", errors="replace").splitlines()
    expected = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()

    total = len(expected)
    if total == 0:
        return 0.0
    matching = sum(a == e for a, e in zip(actual, expected))
    return matching / total
