"""Check 3 - behaviour (weight 4).

Builds the agent's Go program, feeds it the HIDDEN titles (one per line) and
scores the share of output lines that equal the original Python answer
byte for byte. The expected answers were produced by running the original
Python `titlecase()` (tools/gen.py); nobody typed them.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

DATA = Path(os.environ.get("TITLECASE_TESTS_DIR", "/tests")) / "data"
NOBODY = 65534  # run the agent's program unprivileged: it must not read /tests


@criterion(description="share of hidden titles whose output matches the original Python exactly")
def behaviour(workspace: Path) -> float:
    inputs = (DATA / "hidden_inputs.txt").read_bytes()
    expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
    if not expected:
        raise RuntimeError("hidden_expected.txt is empty - broken task")

    tmp = Path(tempfile.mkdtemp(prefix="tcgo-"))
    try:
        os.chmod(tmp, 0o755)
        binary = tmp / "titlecase"
        try:
            built = subprocess.run(["go", "build", "-o", str(binary), "."], cwd=workspace,
                                   capture_output=True, timeout=300)
        except (subprocess.TimeoutExpired, OSError):
            return 0.0
        if built.returncode != 0 or not binary.exists():
            return 0.0
        os.chmod(binary, 0o755)

        extra = {"user": NOBODY, "group": NOBODY} if os.geteuid() == 0 else {}
        try:
            run = subprocess.run([str(binary)], input=inputs, capture_output=True,
                                 timeout=60, cwd=tmp, env={"PATH": "/usr/bin:/bin"}, **extra)
            out = run.stdout
        except subprocess.TimeoutExpired as e:
            out = e.stdout or b""      # score whatever was produced in time
        except OSError:
            return 0.0

        got = out.split(b"\n")
        if got and got[-1] == b"":
            got.pop()
        hits = sum(1 for i, want in enumerate(expected) if i < len(got) and got[i] == want)
        return hits / len(expected)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
