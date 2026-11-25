#!/usr/bin/env python3
"""Generate visible examples and a large, frozen hidden re-exam suite."""
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
SOURCE = Path(
    os.environ.get(
        "TITLECASE_REPO",
        ROOT / "environment" / "python-titlecase",
    )
)
TOOLS = ROOT / "tools"
VISIBLE_COUNT = 2000
HIDDEN_COUNT = 100000


def write_lines(path, lines):
    if any("\n" in line or "\r" in line for line in lines):
        raise ValueError(f"Fixture contains a line break: {path}")
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="")


def main():
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"Reference implementation not found: {SOURCE}")
    seed = int(os.environ.get("TITLECASE_POOL_SEED", secrets.randbits(64)))
    required = VISIBLE_COUNT + HIDDEN_COUNT
    pool_count = required

    with tempfile.TemporaryDirectory(prefix="titlecase-fixtures-") as temp_dir:
        temp = Path(temp_dir)
        pool = temp / "pool.txt"
        frozen = temp / "frozen"
        while True:
            subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "make_pool.py"),
                    str(pool_count),
                    str(seed),
                    str(pool),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "freeze_answers.py"),
                    str(SOURCE),
                    str(pool),
                    str(frozen),
                ],
                check=True,
            )
            inputs = (frozen / "inputs.txt").read_text(encoding="utf-8").splitlines()
            answers = (frozen / "answers.txt").read_text(encoding="utf-8").splitlines()
            if len(inputs) != len(answers):
                raise RuntimeError("Frozen input and answer counts do not match.")
            if len(inputs) >= required:
                break
            pool_count += required - len(inputs) + 1000

        DATA.mkdir(parents=True, exist_ok=True)
        write_lines(DATA / "inputs.txt", inputs[:VISIBLE_COUNT])
        write_lines(DATA / "expected.txt", answers[:VISIBLE_COUNT])
        write_lines(DATA / "hidden_inputs.txt", inputs[VISIBLE_COUNT:required])
        write_lines(DATA / "hidden_expected.txt", answers[VISIBLE_COUNT:required])
        print(
            f"Wrote {VISIBLE_COUNT} visible and {HIDDEN_COUNT} hidden "
            f"stable cases (pool size {pool_count})."
        )


if __name__ == "__main__":
    main()
