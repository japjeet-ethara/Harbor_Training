"""behaviour (weight 4): build the Go program, feed it the HIDDEN inputs, and
score the share of lines that exactly match the hidden expected outputs."""
import os
import subprocess
import tempfile
from pathlib import Path

from rewardkit import criterion


def _data_dir() -> Path:
    try:
        d = Path(__file__).resolve().parent.parent / "data"
        if (d / "hidden_inputs.txt").is_file():
            return d
    except NameError:
        pass
    return Path(os.environ.get("TC_TESTS_DIR", "/tests")) / "data"


def _go_env():
    env = dict(os.environ)
    env.update(GOTOOLCHAIN="local", GOPROXY="off", GOFLAGS="-mod=mod",
               GOWORK="off", CGO_ENABLED="0")
    env.setdefault("GOCACHE", os.path.join(tempfile.gettempdir(), "tc-gocache"))
    env["PATH"] = env.get("PATH", "") + os.pathsep + "/usr/local/go/bin"
    return env


@criterion(description="share of hidden titles whose output matches the reference byte for byte")
def behaviour(workspace: Path) -> float:
    workspace = Path(workspace)
    data = _data_dir()
    inputs = (data / "hidden_inputs.txt").read_bytes()
    expected = (data / "hidden_expected.txt").read_bytes().split(b"\n")
    if expected and expected[-1] == b"":
        expected.pop()
    if not (workspace / "go.mod").is_file():
        return 0.0
    with tempfile.TemporaryDirectory() as tmp:
        binary = os.path.join(tmp, "titlecase")
        try:
            b = subprocess.run(["go", "build", "-o", binary, "."], cwd=workspace,
                               env=_go_env(), capture_output=True, timeout=300)
            if b.returncode != 0:
                return 0.0
            run_kw = {}
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                # Anti-cheat: the answer sheets are only readable by root, and
                # the agent's binary runs as `nobody`, so it cannot read
                # /tests/data at run time and echo the answers back.
                for f in data.glob("*.txt"):
                    os.chmod(f, 0o600)
                os.chmod(tmp, 0o755)
                os.chmod(binary, 0o755)
                run_kw = dict(user=65534, group=65534, extra_groups=[],
                              env={"PATH": "/usr/bin:/bin", "HOME": tmp})
            r = subprocess.run([binary], input=inputs, capture_output=True,
                               cwd=tmp, timeout=120, **run_kw)
        except (OSError, subprocess.TimeoutExpired):
            return 0.0
    actual = r.stdout.split(b"\n")
    if actual and actual[-1] == b"":
        actual.pop()
    matched = sum(1 for i, e in enumerate(expected) if i < len(actual) and actual[i] == e)
    return matched / len(expected) if expected else 0.0
