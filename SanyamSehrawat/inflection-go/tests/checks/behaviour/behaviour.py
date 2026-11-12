"""behaviour (weight 4): share of HIDDEN lines whose output line matches exactly.

The program is built from the agent's repository, fed tests/data/hidden_inputs.txt
on stdin, and its stdout is compared line by line, as bytes, with
tests/data/hidden_expected.txt. A missing, extra or shifted line is a mismatch.

The submitted program is untrusted, so it runs as the unprivileged user `nobody`
with an almost empty environment. That user cannot read /tests (the answers) or
/root (Reward Kit's Python), and the image has no system Python. Anything it
leaves running is killed before the reward is written.
"""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion

GO_ENV = {
    **os.environ,
    "GOFLAGS": "-mod=mod -buildvcs=false",
    "GOPROXY": "off",
    "GOTOOLCHAIN": "local",
    "CGO_ENABLED": "0",
}
DATA = Path(__file__).resolve().parents[2] / "data"


def run_untrusted(exe, lines, folder):
    try:
        return subprocess.run(
            [str(exe)],
            input=lines,
            cwd=folder,
            env={"PATH": "/usr/bin:/bin"},
            user="nobody",
            group="nogroup",
            capture_output=True,
            timeout=120,
        ).stdout
    finally:
        subprocess.run(["pkill", "-KILL", "-u", "nobody"], capture_output=True, timeout=30)


@criterion(description="share of hidden lines answered exactly like the original")
def behaviour(workspace: Path) -> float:
    try:
        expected = (DATA / "hidden_expected.txt").read_bytes().split(b"\n")[:-1]
        lines = (DATA / "hidden_inputs.txt").read_bytes()
        if not (workspace / "go.mod").is_file():
            return 0.0
        with tempfile.TemporaryDirectory() as tmp:
            os.chmod(tmp, 0o755)
            exe = Path(tmp) / "inflection"
            built = subprocess.run(
                ["go", "build", "-o", str(exe), "."], cwd=workspace, env=GO_ENV, capture_output=True, timeout=300
            )
            if built.returncode != 0 or not exe.is_file():
                return 0.0
            os.chmod(exe, 0o755)
            output = run_untrusted(exe, lines, tmp)
        actual = output.split(b"\n")
        if actual and actual[-1] == b"":
            actual.pop()
        matched = sum(1 for got, want in zip(actual, expected) if got == want)
        return matched / max(len(expected), len(actual))
    except Exception:
        return 0.0
