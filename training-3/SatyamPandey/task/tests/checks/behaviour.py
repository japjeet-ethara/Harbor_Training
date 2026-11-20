"""Check `behaviour` (weight 1, the only scored check): output on hidden titles.

Day 5 hardening:
  * Gate (cheats 1 and 2): 0 unless the hard rules hold and the program builds.
  * Sandbox (cheat 3): the agent's program runs under Reward Kit's Worker, as a fresh
    unprivileged user that cannot read /tests (the answers), /logs/verifier or
    /workspace. Answers are read into memory before it starts; it only gets stdin.
  * Exam: tests/data/inputs.txt + answers.txt, 100,000 titles frozen twice from the
    original titlecase WITH the `regex` package (kit/answers.py, see kit/report.txt).
  * Fresh sample (lookup tables): those answers are public, so every run also grades
    5,000 brand-new titles whose answers the original computes now (fresh.py).
  * Score: share = exact lines; curve(share) = max(0, (share - 0.9) / 0.1);
    reward = min(curve(frozen share), curve(fresh share)).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import rewardkit as rk

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fresh import fresh_exam  # noqa: E402
from rules import go_build, rules_ok  # noqa: E402

DATA = Path("/tests/data")
FLOOR = 0.9
N_FRESH = 5000
PRIVATE = (Path("/tests"), Path("/logs/verifier"), Path("/workspace"))


def _lines(path: Path) -> list[bytes]:
    # No title contains "\r", so CRLF can only come from a Windows checkout.
    data = path.read_bytes().replace(b"\r\n", b"\n")
    assert data.endswith(b"\n"), f"{path} must end with a newline"
    return data[:-1].split(b"\n")


def _curve(matches: int, total: int) -> float:
    return max(0.0, (matches / total - FLOOR) / (1.0 - FLOOR))


@rk.criterion(description="min over the 100,000 frozen titles and 5,000 fresh titles of "
                          "max(0, (exact share - 0.9) / 0.1); 0 if the rules fail")
def behaviour(workspace) -> float:
    # Prepare every answer first, while the agent's code has not run yet.
    inputs = _lines(DATA / "inputs.txt")
    expected = _lines(DATA / "answers.txt")
    assert len(inputs) == len(expected) >= 100_000, "exam files are incomplete"
    seed, fresh_in, fresh_ans = fresh_exam([t.decode("utf-8") for t in inputs], N_FRESH)
    assert len(fresh_in) >= N_FRESH * 0.99, "the original was unstable on the fresh titles"
    print(f"fresh sample seed {seed}: {len(fresh_in)} titles", file=sys.stderr)
    fresh_in = [t.encode("utf-8") for t in fresh_in]
    fresh_ans = [t.encode("utf-8") for t in fresh_ans]

    ok, reason = rules_ok(workspace)
    if not ok:
        print(f"rules failed: {reason}", file=sys.stderr)
        return 0.0

    build_dir = tempfile.mkdtemp(prefix="tc-build-")          # mode 0700, root only
    try:
        binary = os.path.join(build_dir, "titlecase_bin")
        if not go_build(workspace, binary, ".") or not os.path.isfile(binary):
            return 0.0
        worker = rk.Worker(private_paths=PRIVATE, max_output_bytes=64 * 2**20)
        stdin = b"\n".join(inputs + fresh_in) + b"\n"
        try:
            result = worker.run("exec ./titlecase_bin", files=[Path(binary)],
                                stdin=stdin, timeout_sec=120)
        except rk.WorkerError:                                 # timeout / too much output
            return 0.0
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)

    got = result.stdout.split(b"\n")
    if got and got[-1] == b"":
        got = got[:-1]
    n = len(inputs)
    frozen_ok = sum(1 for i, exp in enumerate(expected) if i < len(got) and got[i] == exp)
    fresh_ok = sum(1 for i, exp in enumerate(fresh_ans) if n + i < len(got) and got[n + i] == exp)
    print(f"frozen {frozen_ok}/{n}, fresh {fresh_ok}/{len(fresh_ans)}", file=sys.stderr)
    return min(_curve(frozen_ok, n), _curve(fresh_ok, len(fresh_ans)))
