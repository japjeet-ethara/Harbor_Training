"""Count how many answers a port gets wrong, and how likely a smaller random suite was to notice.

Usage: python compare.py <suite_dir> <port_output.txt> [small_suite_size]
port_output.txt = what the port printed for suite_dir/inputs.txt, one line per input.
"""
import math
import sys
from pathlib import Path


def records(path):
    data = Path(path).read_bytes()
    return data.removesuffix(b"\n").split(b"\n") if data else []


def main():
    suite_dir, got_file = sys.argv[1], sys.argv[2]
    small = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    sys.stdout.reconfigure(encoding="utf-8")
    inputs = records(f"{suite_dir}/inputs.txt")
    want = records(f"{suite_dir}/answers.txt")
    got = records(got_file)
    if len(inputs) != len(want):
        raise ValueError("input and answer files have different line counts")
    bad = [i for i, expected in enumerate(want) if i >= len(got) or got[i] != expected]
    n, b = len(want), len(bad)
    miss = math.comb(n - b, small) / math.comb(n, small) if small <= n - b else 0.0
    print(f"wrong answers      {b} of {n}")
    if len(got) != n:
        print(f"output lines       {len(got)} for {n} inputs")
    print(f"chance a random {small} suite sees none of them: {miss:.0%}")
    for i in bad[:5]:
        value = got[i].decode("utf-8", errors="backslashreplace") if i < len(got) else None
        print(f"  input {inputs[i].decode('utf-8')!r}\n  want  {want[i].decode('utf-8')!r}\n  got   {value!r}")


if __name__ == "__main__":
    main()
