"""Shared grading code for the three checks.

Every check calls behaviour_score(). build and no_python only pay when the
program also gets real titles right, so an empty program that compiles, or a
"delete the .py files" solution, earns nothing from them.

This file lives in /tests/lib, outside /tests/checks, so Reward Kit does not
treat it as a check of its own. Nothing is cached between checks: a cache file
would sit in a folder the graded program could write to first.
"""
import os
import subprocess
import tempfile
import time
from pathlib import Path

# 101,958 titles: the 100,000 from kit/make_pool.py (count 100000, seed 1),
# then the 1,958 titles of the old 2,000-title hidden exam that were not
# already in that pool (it has Unicode the kit pool lacks, such as ŉ, ﬁ, ß).
# Answers frozen twice by kit/answers.py from titlecase WITHOUT regex (re mode).
HIDDEN_INPUTS = Path("/tests/data/inputs.txt")
HIDDEN_EXPECTED = Path("/tests/data/answers.txt")
NOBODY = 65534

# Below this share of exact matches, behaviour scores 0. From FLOOR to 100 %
# the score rises in a straight line from 0 to 1. A port that is right on only
# half of the titles is not a working port, so it gets no credit.
FLOOR = 0.5


def _live_nobody_pids() -> list[int]:
    """PIDs of processes still running as nobody (zombies do not count)."""
    pids = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "status").read_text()
        except OSError:
            continue
        fields = dict(
            line.split(":", 1) for line in status.splitlines() if ":" in line
        )
        uid = fields.get("Uid", "").split()
        state = fields.get("State", "").strip()
        if uid and int(uid[0]) == NOBODY and not state.startswith("Z"):
            pids.append(int(entry.name))
    return pids


def kill_leftovers() -> None:
    """Kill every process the graded program left behind.

    The program runs as nobody and may start a detached child that keeps
    running after it exits (for example to overwrite
    /logs/verifier/reward.json after Reward Kit writes the real score).
    `kill -9 -1` run as nobody signals every process nobody owns. Repeat
    until none is left, in case one was forking while we killed.
    """
    for _ in range(100):
        subprocess.run(
            ["/bin/kill", "-9", "-1"],
            capture_output=True,
            cwd="/",
            env={},
            user=NOBODY,
            group=NOBODY,
            extra_groups=[],
            timeout=10,
        )
        if not _live_nobody_pids():
            return
        time.sleep(0.05)
    raise RuntimeError("processes owned by nobody survived kill -9 -1")


def go_build_all(workspace: Path) -> bool:
    """`go build ./...` passes in the repository."""
    build = subprocess.run(
        ["go", "build", "./..."], cwd=workspace, capture_output=True, timeout=300
    )
    if build.returncode != 0:
        print(build.stderr.decode(errors="replace"))
    return build.returncode == 0


def has_python_files(workspace: Path) -> bool:
    return any(workspace.rglob("*.py"))


def match_share(workspace: Path) -> float:
    """Share of hidden titles whose output matches the original exactly."""
    with tempfile.TemporaryDirectory() as folder:
        os.chmod(folder, 0o755)
        program = Path(folder) / "titlecase"
        build = subprocess.run(
            ["go", "build", "-o", str(program), "."],
            cwd=workspace,
            capture_output=True,
            timeout=300,
        )
        if build.returncode != 0:
            print(build.stderr.decode(errors="replace"))
            return 0.0

        # Split on \n only: titles may hold \x85, U+2028 and other characters
        # that str.splitlines() would treat as line ends.
        expected = HIDDEN_EXPECTED.read_bytes().split(b"\n")[:-1]
        try:
            with HIDDEN_INPUTS.open("rb") as titles:
                run = subprocess.run(
                    [str(program)],
                    stdin=titles,
                    capture_output=True,
                    cwd="/",
                    env={},
                    user=NOBODY,
                    group=NOBODY,
                    extra_groups=[],
                    timeout=120,
                )
        except subprocess.TimeoutExpired:
            return 0.0
        finally:
            # Runs on every path, before any score is returned, so nothing the
            # program started can outlive this run and touch the reward files.
            kill_leftovers()
        if run.returncode != 0:
            return 0.0

        # Only lines that end in \n count as output lines. A last piece with no
        # \n after it is an unfinished line: it is never a match, but it still
        # counts as one output line.
        *actual, tail = run.stdout.split(b"\n")
        printed = len(actual) + (1 if tail else 0)
        matched = sum(got == want for got, want in zip(actual, expected))
        # Divide by the larger of the two line counts, so every missing or
        # extra output line counts as one wrong answer. zip() alone would stop
        # at the shorter list and never see lines printed after the last title.
        total = max(len(expected), printed)
        share = matched / total
        print(
            f"matched {matched} of {len(expected)} hidden titles, "
            f"printed {printed} lines ({share:.4%})"
        )
        return share


def behaviour_score(workspace: Path) -> float:
    """0 below FLOOR, then a straight line up to 1.0 at a perfect match."""
    share = match_share(workspace)
    if share >= 1.0:
        return 1.0
    if share <= FLOOR:
        return 0.0
    return (share - FLOOR) / (1.0 - FLOOR)
