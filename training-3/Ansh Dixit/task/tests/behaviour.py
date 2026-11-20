"""Check 3 (weight 4): share of hidden lines whose output matches Python exactly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rewardkit as rk
from _common import build_binary, run

DATA = Path("/tests/data")


@rk.criterion(description="share of hidden lines that match the original byte for byte")
def behaviour(workspace: Path) -> float:
    exe = "/tmp/behaviour_check_bin"
    if not build_binary(exe):
        return 0.0
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    p = run([exe], cwd="/tmp", timeout=120, stdin=inputs)
    if p is None or p.returncode != 0:
        return 0.0
    got = p.stdout.split(b"\n")
    good = sum(1 for i, e in enumerate(expected) if i < len(got) and got[i] == e)
    return good / len(expected)


rk.behaviour()
