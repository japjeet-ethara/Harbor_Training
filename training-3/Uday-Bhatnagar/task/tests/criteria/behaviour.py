"""Run the submitted Go port and score exact output against three input sets."""

from __future__ import annotations

import json
import os
import random
import signal
import string
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TESTS_DIR / "criteria"), str(TESTS_DIR / "reference")]
from _lib import build_port, compare_lines  # noqa: E402
from titlecase import REGEX_AVAILABLE, titlecase  # noqa: E402

DATA_DIR = TESTS_DIR / "data"
FRESH_COUNT = 2000
RUN_TIMEOUT_SEC = 120
OUTPUT_LIMIT = 16 * 1024 * 1024


def fresh_exam(frozen_inputs: bytes) -> tuple[bytes, bytes]:
    if REGEX_AVAILABLE:
        raise RuntimeError("the reference must use the standard-library re mode")
    rng = random.SystemRandom()
    pool = frozen_inputs.decode("utf-8").split("\n")[:-1]
    titles = []
    for first, second in zip(rng.sample(pool, FRESH_COUNT), rng.sample(pool, FRESH_COUNT)):
        word = "".join(rng.choices(string.ascii_lowercase, k=12))
        titles.append(f"{first} {word} {second}")
    inputs = "".join(title + "\n" for title in titles).encode("utf-8")
    answers = "".join(titlecase(title) + "\n" for title in titles).encode("utf-8")
    return inputs, answers


def run_port(jail: Path, inputs: bytes) -> bytes:
    # The temporary root contains only the static Go binary. No interpreter,
    # workspace, /proc, or verifier files are mounted inside it.
    with tempfile.TemporaryFile() as output:
        with subprocess.Popen(
            [
                "prlimit", f"--fsize={OUTPUT_LIMIT}", "--",
                "setpriv", "--no-new-privs",
                "chroot", "--userspec=65534:65534", "--groups=65534",
                str(jail), "/port",
            ],
            cwd="/",
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        ) as proc:
            try:
                proc.communicate(inputs, timeout=RUN_TIMEOUT_SEC)
                if proc.returncode:
                    raise RuntimeError(f"program exited with status {proc.returncode}")
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        output.seek(0)
        return output.read()


def grade(workspace: Path) -> tuple[float, str]:
    if not workspace.is_dir():
        return 0.0, "submitted workspace is missing"
    if any(entry.is_file() or entry.is_symlink() for entry in workspace.rglob("*.py")):
        return 0.0, "Python source remains in the submitted workspace"

    try:
        with tempfile.TemporaryDirectory(prefix="titlecase-verify-") as tmp:
            build_dir = Path(tmp) / "build"
            build_dir.mkdir()
            jail = Path(tmp) / "runtime"
            jail.mkdir()
            build_port(workspace, build_dir, jail / "port")
            frozen_inputs = (DATA_DIR / "inputs.txt").read_bytes()
            exams = (
                ("original", (DATA_DIR / "hidden_inputs.txt").read_bytes(),
                 (DATA_DIR / "hidden_expected.txt").read_bytes()),
                ("frozen", frozen_inputs, (DATA_DIR / "answers.txt").read_bytes()),
                ("fresh", *fresh_exam(frozen_inputs)),
            )
            scores = []
            details = []
            for name, inputs, expected in exams:
                actual = run_port(jail, inputs)
                correct, total = compare_lines(expected, actual)
                scores.append(correct / total)
                details.append(f"{name}: {correct}/{total} exact matches")
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        return 0.0, str(exc)

    return min(scores), " | ".join(details)


if __name__ == "__main__":
    workspace, reward_file = map(Path, sys.argv[1:])
    score, details = grade(workspace)
    print(details)
    print(f"reward: {score}")
    reward_file.write_text(json.dumps({"reward": score}) + "\n", encoding="utf-8")
