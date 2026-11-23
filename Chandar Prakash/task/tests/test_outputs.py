import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path("/workspace/repo")
TEST_DATA = Path("/tests/data")
REWARD_PATH = Path("/logs/verifier/reward.json")


def has_python_files():
    for root, _, files in os.walk(REPO):
        if any(Path(filename).suffix.lower() == ".py" for filename in files):
            return True
    return False


def split_lines(data):
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def behavior_score():
    inputs = (TEST_DATA / "inputs.txt").read_bytes()
    input_lines = split_lines(inputs)
    expected = split_lines((TEST_DATA / "answers.txt").read_bytes())

    if len(input_lines) != 100_000 or len(expected) != 100_000:
        print(
            "The frozen behavior suite must contain exactly 100,000 input/answer lines.",
            file=sys.stderr,
        )
        return 0.0
    if len(input_lines) != len(expected):
        print("Input and answer files have different line counts.", file=sys.stderr)
        return 0.0

    with tempfile.TemporaryDirectory() as temp_dir:
        binary = Path(temp_dir) / "titlecase"
        build = subprocess.run(
            ["go", "build", "-o", str(binary), "."],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if build.returncode != 0:
            print("Could not build the root Go program for behavior check.", file=sys.stderr)
            sys.stderr.buffer.write(build.stderr)
            return 0.0

        os.chmod(temp_dir, 0o755)
        os.chmod(binary, 0o755)

        try:
            result = subprocess.run(
                [str(binary)],
                cwd=REPO,
                input=inputs,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False,
                user=65534,
                group=65534,
                extra_groups=[],
            )
        except subprocess.TimeoutExpired:
            print("Go program exceeded the behavior check timeout.", file=sys.stderr)
            return 0.0

    if result.returncode != 0:
        print("Go program returned a non-zero exit status.", file=sys.stderr)
        sys.stderr.buffer.write(result.stderr)
        return 0.0

    actual = split_lines(result.stdout)
    if len(actual) != len(expected):
        print(
            "Go program emitted {} lines for {} inputs.".format(
                len(actual), len(expected)
            ),
            file=sys.stderr,
        )
        return 0.0
    if not expected:
        return 1.0 if not actual else 0.0
    matches = sum(got == want for got, want in zip(actual, expected))
    return matches / len(expected)


def main():
    build = subprocess.run(
        ["go", "build", "./..."],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    build_score = 1.0 if build.returncode == 0 else 0.0
    if build.returncode != 0:
        print("go build ./... failed.", file=sys.stderr)
        sys.stderr.buffer.write(build.stderr)

    no_python_score = 1.0 if build_score == 1.0 and not has_python_files() else 0.0
    behavior = (
        behavior_score()
        if build_score == 1.0 and no_python_score == 1.0
        else 0.0
    )
    reward = behavior

    REWARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REWARD_PATH.open("w", encoding="utf-8") as reward_file:
        json.dump({"reward": reward}, reward_file)
        reward_file.write("\n")

    print(
        "Check scores: build={:.6f}, no_python={:.6f}, behaviour={:.6f}; "
        "weighted reward={:.6f}".format(build_score, no_python_score, behavior, reward),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
