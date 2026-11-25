"""Check a port's output on the regression suite, byte for byte (no normalisation).

Usage: python -I -B check_regression.py <suite_dir> <labels.tsv> <got.txt>
Prints every case with escaped input; for a mismatch, prints want/got as escaped
text and as code points. Exit 1 if any required case fails.
"""
import sys


def records(path):
    data = open(path, "rb").read()
    if data.endswith(b"\n"):
        data = data[:-1]
    return data.split(b"\n") if data else []


def cps(b):
    return " ".join(f"U+{ord(c):04X}" for c in b.decode("utf-8", errors="surrogateescape"))


def esc(b):
    return ascii(b.decode("utf-8", errors="surrogateescape"))


def main():
    suite, labels_path, got_path = sys.argv[1:4]
    inputs, want, got = records(f"{suite}/inputs.txt"), records(f"{suite}/answers.txt"), records(got_path)
    labels = [line.rstrip("\n").split("\t") for line in open(labels_path, encoding="utf-8")]
    assert len(inputs) == len(want) == len(labels), "suite and labels differ in length"
    print(f"records: inputs {len(inputs)}, answers {len(want)}, output {len(got)}")
    req_fail = req_total = res_fail = 0
    for i, (num, group, req, note) in enumerate(labels):
        g = got[i] if i < len(got) else b"<missing>"
        ok = g == want[i]
        required = req == "1"
        req_total += required
        if not ok:
            req_fail += required
            res_fail += not required
        tag = "PASS" if ok else ("FAIL" if required else "DIFF (residual, not required)")
        print(f"{tag:5} #{num:>2} [{group}] {note}: input {esc(inputs[i])}")
        if not ok:
            print(f"        want {esc(want[i])}  [{cps(want[i])}]")
            print(f"        got  {esc(g)}  [{cps(g)}]")
    print(f"required: {req_total - req_fail}/{req_total} pass; residual cases differing: {res_fail}/{len(labels) - req_total}")
    sys.exit(1 if req_fail else 0)


if __name__ == "__main__":
    main()
