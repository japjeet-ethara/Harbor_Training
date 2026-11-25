#!/usr/bin/env python3
"""Compare port output against frozen answers and compute probability of missing errors on a smaller sample."""

import math
from pathlib import Path
import sys


def compute_miss_probability(N: int, k: int, s: int) -> float:
    """Hypergeometric probability of drawing s items from N with 0 defects when there are k defects."""
    if k == 0:
        return 1.0
    if N - k < s:
        return 0.0
    # Calculate in log space to avoid overflow / precision loss
    log_p = 0.0
    for i in range(s):
        log_p += math.log(N - k - i) - math.log(N - i)
    return math.exp(log_p)


def main():
    if len(sys.argv) < 3:
        print("Usage: compare.py <key_dir> <got.txt> [small_sample_size]", file=sys.stderr)
        sys.exit(1)

    key_dir = Path(sys.argv[1]).resolve()
    got_file = Path(sys.argv[2]).resolve()
    sample_size = int(sys.argv[3]) if len(sys.argv) > 3 else 2000

    answers_file = key_dir / "answers.txt"
    if not answers_file.is_file():
        # Fallback if key_dir is the answers file itself
        if key_dir.is_file():
            answers_file = key_dir

    with open(answers_file, "r", encoding="utf-8") as f:
        expected = [line.strip("\r\n") for line in f]

    with open(got_file, "r", encoding="utf-8") as f:
        actual = [line.strip("\r\n") for line in f]

    total = len(expected)
    if len(actual) < total:
        print(f"Warning: actual has only {len(actual)} lines vs {total} expected", file=sys.stderr)

    wrong_count = 0
    wrong_samples = []

    for i in range(total):
        exp = expected[i]
        act = actual[i] if i < len(actual) else "<MISSING>"
        if exp != act:
            wrong_count += 1
            if len(wrong_samples) < 5:
                wrong_samples.append((i, exp, act))

    correct_count = total - wrong_count
    accuracy = (correct_count / total) * 100.0

    if wrong_count == 0:
        chance_miss = 100.0
    else:
        prob = compute_miss_probability(total, wrong_count, sample_size)
        chance_miss = prob * 100.0

    print(f"Total titles:             {total}")
    print(f"Correct:                  {correct_count} ({accuracy:.2f}%)")
    print(f"Wrong:                    {wrong_count}")
    if wrong_count == 0:
        print(f"Chance 2K random misses:  n/a (0 errors)")
    else:
        print(f"Chance 2K random misses:  {chance_miss:.2f}%")

    if wrong_samples:
        print("\nFirst wrong samples:")
        for idx, exp, act in wrong_samples:
            print(f"  Line {idx + 1}:")
            print(f"    Expected: {exp}")
            print(f"    Got:      {act}")


if __name__ == "__main__":
    main()
