"""Freeze the original titlecase answers from two independent processes."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def records(path):
    data = path.read_bytes()
    if not data.endswith(b"\n") or b"\r" in data:
        raise ValueError(f"{path} must contain LF-terminated records")
    return data[:-1].decode("utf-8").split("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("pool", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()

    titles = records(args.pool)
    if args.worker:
        sys.path.insert(0, str(args.reference.resolve()))
        import titlecase

        print(json.dumps({
            "regex": titlecase.REGEX_AVAILABLE,
            "answers": [titlecase.titlecase(title) for title in titles],
        }))
        return

    runs = []
    for seed in (1, 2):
        env = dict(os.environ, PYTHONHASHSEED=str(seed))
        command = [
            sys.executable, "-P", "-s", "-B", str(Path(__file__).resolve()),
            str(args.reference), str(args.pool), str(args.output), "--worker",
        ]
        runs.append(json.loads(subprocess.check_output(command, env=env)))
    first, second = runs
    if first["regex"] != second["regex"]:
        raise RuntimeError("Reference processes used different regex modes")

    args.output.mkdir(parents=True, exist_ok=True)
    kept = 0
    with (args.output / "inputs.txt").open("w", encoding="utf-8", newline="\n") as inputs, \
         (args.output / "answers.txt").open("w", encoding="utf-8", newline="\n") as answers:
        for title, left, right in zip(titles, first["answers"], second["answers"], strict=True):
            if left != right:
                continue
            if "\n" in left or "\r" in left:
                raise ValueError("Reference returned more than one output line")
            inputs.write(title + "\n")
            answers.write(left + "\n")
            kept += 1
    mode = "regex" if first["regex"] else "re"
    report = (
        f"Pool inputs: {len(titles)}\nStable answers: {kept}\n"
        f"Unstable answers dropped: {len(titles) - kept}\n"
        f"Reference: CPython {sys.version.split()[0]}, {mode} mode\n"
    )
    (args.output / "report.txt").write_text(report, encoding="utf-8", newline="\n")
    print(report, end="")


if __name__ == "__main__":
    main()
