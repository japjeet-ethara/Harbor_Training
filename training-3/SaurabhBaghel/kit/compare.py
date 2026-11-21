"""Count wrong answers and estimate whether a 2,000-title exam misses them."""
import math
import sys


def main():
    suite_dir, got_file = sys.argv[1], sys.argv[2]
    small = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    inputs = open(f"{suite_dir}/inputs.txt", encoding="utf-8").read().split("\n")[:-1]
    want = open(f"{suite_dir}/answers.txt", encoding="utf-8").read().split("\n")[:-1]
    got = open(got_file, encoding="utf-8", errors="replace").read().split("\n")
    if len(got) < len(want):
        print(f"port printed {len(got)} lines for {len(want)} inputs: it crashed or stopped early")
        sys.exit(1)
    bad = [i for i in range(len(want)) if got[i] != want[i]]
    n, b = len(want), len(bad)
    miss = math.comb(n - b, small) / math.comb(n, small) if small <= n - b else 0.0
    print(f"wrong answers      {b} of {n}")
    print(f"chance a random {small} suite sees none of them: {miss:.0%}")
    for i in bad[:5]:
        print(f"  input {inputs[i]!r}\n  want  {want[i]!r}\n  got   {got[i]!r}")


if __name__ == "__main__":
    main()
