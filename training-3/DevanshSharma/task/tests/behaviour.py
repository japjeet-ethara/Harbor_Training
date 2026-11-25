import os
import subprocess
from pathlib import Path

from rewardkit import criterion

HIDDEN_INPUTS   = Path("/tests/data/inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/answers.txt")


@criterion
def behaviour(workspace: Path) -> float:
    if not workspace.is_dir():
        return 0.0

    has_program = any(
        path.is_file() and path.suffix == ".go" and not path.name.endswith("_test.go")
        for path in workspace.rglob("*")
    )
    if not has_program:
        return 0.0

    expected_lines = HIDDEN_EXPECTED.read_text(encoding="utf-8").splitlines()
    if not expected_lines:
        return 0.0

    cache   = Path("/tmp/gocache-behaviour")
    binary  = Path("/tmp/titlecase-behaviour")
    env = os.environ.copy()
    env["GOCACHE"]    = str(cache / "cache")
    env["GOMODCACHE"] = str(cache / "mod")
    env["GOPROXY"]    = "off"
    env["GONOSUMDB"]  = "*"

    build = subprocess.run(
        ["go", "build", "-o", str(binary), "."],
        cwd=workspace,
        env=env,
        capture_output=True,
        timeout=120,
    )
    if build.returncode != 0 or not binary.is_file():
        return 0.0

    # Lock answer files before the candidate binary can read them, then
    # run the binary as an unprivileged user so it cannot open them.
    binary.chmod(0o755)
    for locked in (HIDDEN_EXPECTED, HIDDEN_INPUTS.parent / "inputs.txt"):
        if locked.exists():
            locked.chmod(0o600)

    with HIDDEN_INPUTS.open(encoding="utf-8", newline="\n") as fh:
        run = subprocess.run(
            ["su", "candidate", "-s", "/bin/sh", "-c", str(binary)],
            stdin=fh,
            capture_output=True,
            timeout=120,
        )
    if run.returncode != 0:
        return 0.0

    actual_lines = run.stdout.decode("utf-8", errors="replace").splitlines()
    matches = sum(
        1
        for i, expected in enumerate(expected_lines)
        if i < len(actual_lines) and actual_lines[i] == expected
    )
    extra = len(actual_lines) - len(expected_lines)
    if extra > 0:
        matches -= extra
    if matches < 0:
        matches = 0
    score = matches / len(expected_lines)
    # Require at least 50% correct before awarding any partial credit.
    # This prevents a do-nothing/invariance-cheat from earning points
    # purely through titlecase-invariant inputs.
    if score < 0.5:
        return 0.0
    return score
