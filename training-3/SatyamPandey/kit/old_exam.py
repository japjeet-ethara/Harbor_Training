"""Score a port on my OLD exam (the 2,000 hidden titles graded before Day 5).

Usage: python old_exam.py <old_exam_dir> <got-old.txt>
old_exam_dir holds hidden_inputs.txt / hidden_expected.txt (measure/old-exam/);
got-old.txt is what the port printed for hidden_inputs.txt, one line per input.
Prints the number of wrong lines and whether the old exam caught the port.
"""
import sys


def lines(path):
    return open(path, encoding="utf-8", errors="replace", newline="\n").read().split("\n")


def main():
    old_dir, got_file = sys.argv[1], sys.argv[2]
    want = lines(f"{old_dir}/hidden_expected.txt")[:-1]
    got = lines(got_file)
    bad = [i for i in range(len(want)) if i >= len(got) or got[i] != want[i]]
    print(f"old exam wrong     {len(bad)} of {len(want)}")
    print(f"old exam caught it: {'yes' if bad else 'no'}")


if __name__ == "__main__":
    main()
