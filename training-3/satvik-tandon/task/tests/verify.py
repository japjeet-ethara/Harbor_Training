"""Grade a standalone Go program against the frozen titlecase corpus."""

import json
import os
import resource
import subprocess
import tempfile
from pathlib import Path

DATA = Path("/tests/data")
SCORE_FILE = Path("/logs/verifier/reward.json")
BUILD_ENV = dict(
    os.environ,
    CGO_ENABLED="0",
    GOENV="off",
    GOFLAGS="",
    GOPROXY="off",
    GOTOOLCHAIN="local",
    GOWORK="off",
)


def run_build(*args):
    result = subprocess.run(
        ["go", "build", *args], env=BUILD_ENV, capture_output=True, timeout=120
    )
    if result.returncode:
        print(result.stderr.decode("utf-8", errors="replace"))
    return result.returncode == 0


def run_submission(jail, inputs, max_output):
    def limit_output():
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_output, max_output))

    # chroot changes the root and working directory before dropping to nobody.
    # The executable receives only the test input stream and an empty filesystem.
    with tempfile.TemporaryFile() as stdout:
        result = subprocess.run(
            ["/usr/sbin/chroot", "--userspec=65534:65534", "--groups=65534",
             str(jail), "/titlecase"],
            env={"PATH": "/", "LANG": "C.UTF-8"},
            input=inputs,
            stdout=stdout,
            stderr=subprocess.DEVNULL,
            preexec_fn=limit_output,
            timeout=120,
        )
        if result.returncode:
            print(f"Submission exited with status {result.returncode}")
            return None
        stdout.seek(0)
        return stdout.read(max_output + 1)


def grade(scores):
    inputs = (DATA / "inputs.txt").read_bytes()
    expected = (DATA / "answers.txt").read_bytes()
    if not expected.endswith(b"\n") or inputs.count(b"\n") != expected.count(b"\n"):
        raise ValueError("Verifier fixture inputs and answers must have matching line counts")
    expected_lines = expected[:-1].split(b"\n")

    if not run_build("./..."):
        return
    scores["build"] = 1.0
    if any(Path.cwd().rglob("*.py")):
        return
    scores["no_python"] = 1.0

    with tempfile.TemporaryDirectory(prefix="titlecase-root-") as root:
        jail = Path(root)
        jail.chmod(0o755)
        if not run_build("-o", str(jail / "titlecase"), "."):
            scores["build"] = 0.0
            return
        actual = run_submission(jail, inputs, max(1 << 20, 4 * len(expected)))

    if actual is None or not actual.endswith(b"\n"):
        return
    actual_lines = actual[:-1].split(b"\n")
    if len(actual_lines) != len(expected_lines):
        print(f"Expected {len(expected_lines)} lines, got {len(actual_lines)}")
        return
    scores["behaviour"] = sum(a == b for a, b in zip(actual_lines, expected_lines)) / len(expected_lines)
    scores["reward"] = scores["behaviour"]


def main():
    scores = dict.fromkeys(("build", "no_python", "behaviour", "reward"), 0.0)
    try:
        grade(scores)
    except subprocess.TimeoutExpired:
        print("Build or submission timed out")
    SCORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCORE_FILE.write_text(json.dumps(scores) + "\n", encoding="utf-8")
    print(json.dumps(scores))


if __name__ == "__main__":
    main()
