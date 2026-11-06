import subprocess
from pathlib import Path
import rewardkit as rk
from rewardkit import criterion

DATA = Path(__file__).resolve().parent / "data"

@criterion(description="share of hidden titles cased exactly like the Python original")
def matches_python(workspace: Path) -> float:
    binary = "/tmp/titlecase-under-test"
    try:
        b = subprocess.run(["go", "build", "-o", binary, "."], cwd=workspace,
                           capture_output=True, timeout=600)
        if b.returncode != 0:
            return 0.0
        inputs = (DATA / "hidden_inputs.txt").read_bytes()
        run = subprocess.run([binary], input=inputs, capture_output=True, timeout=120)
    except Exception:
        return 0.0
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    actual = run.stdout.split(b"\n")
    good = sum(1 for i, e in enumerate(expected) if i < len(actual) and actual[i] == e)
    return good / len(expected)

rk.matches_python()
