"""Measure a port against an LF-terminated titlecase exam."""

import argparse
import itertools
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("sample", type=int, nargs="?", default=2000)
    args = parser.parse_args()

    inputs = (args.suite / "inputs.txt").read_bytes().splitlines(keepends=True)
    expected = (args.suite / "answers.txt").read_bytes().splitlines(keepends=True)
    actual = args.output.read_bytes().splitlines(keepends=True)
    if len(expected) != len(inputs) or not 0 <= args.sample <= len(inputs):
        parser.error("invalid suite or sample size")
    differences = [
        n for n, (want, got) in enumerate(itertools.zip_longest(expected, actual))
        if want != got
    ]
    wrong = sum(index < len(expected) for index in differences)
    total = len(expected)
    miss = (math.comb(total - wrong, args.sample) / math.comb(total, args.sample)
            if args.sample <= total - wrong else 0.0)
    print(f"wrong answers: {wrong} of {total}")
    print(f"extra output records: {max(0, len(actual) - total)}")
    print(f"chance a random {args.sample}-title sample misses every error: {miss:.6%}")
    for index in differences[:5]:
        if index < total:
            got = actual[index] if index < len(actual) else None
            print(f"  input={inputs[index]!r} expected={expected[index]!r} actual={got!r}")


if __name__ == "__main__":
    main()
