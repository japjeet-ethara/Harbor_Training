"""Run a built Go titlecase binary on an input file and show the first 10
lines that differ from the expected file.

    python tools/compare.py <binary> tests/data/inputs.txt tests/data/expected.txt
"""

import subprocess
import sys


def main() -> None:
    binary, inputs_path, expected_path = sys.argv[1:4]
    with open(inputs_path, "rb") as f:
        data = f.read()
    with open(expected_path, "rb") as f:
        expected = f.read().decode("utf-8").split("\n")[:-1]
    inputs = data.decode("utf-8").split("\n")[:-1]

    proc = subprocess.run([binary], input=data, capture_output=True, timeout=120)
    got = proc.stdout.decode("utf-8", errors="replace").split("\n")
    if got and got[-1] == "":
        got = got[:-1]

    wrong = [i for i in range(len(expected)) if i >= len(got) or got[i] != expected[i]]
    print(f"{len(expected) - len(wrong)}/{len(expected)} lines match")
    for i in wrong[:10]:
        actual = got[i] if i < len(got) else "<missing>"
        print(f"line {i + 1}\n  input:    {inputs[i]!r}\n  expected: {expected[i]!r}\n  actual:   {actual!r}")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
