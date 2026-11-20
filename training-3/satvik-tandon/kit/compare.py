"""Count how many answers a port gets wrong, and how likely a smaller random suite was to notice.

Usage: python compare.py <suite_dir> <port_output.txt> [small_suite_size]
port_output.txt = what the port printed for suite_dir/inputs.txt, one line per input.
"""
import math
import sys


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    suite_dir, got_file = sys.argv[1], sys.argv[2]
    small = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    inputs = open(f"{suite_dir}/inputs.txt", encoding="utf-8").read().split("\n")[:-1]
    want = open(f"{suite_dir}/answers.txt", encoding="utf-8").read().split("\n")[:-1]
    got = open(got_file, encoding="utf-8", errors="strict").read().removesuffix("\n").split("\n")
    if len(got) != len(want):
        print(f"port printed {len(got)} lines for {len(want)} inputs")
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
