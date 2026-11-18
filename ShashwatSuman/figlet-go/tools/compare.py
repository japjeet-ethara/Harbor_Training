"""Run a built figlet binary on a .jsonl answer file and show the first 5
cases that differ (args, expected, actual).

    python tools/compare.py <binary> tests/data/visible.jsonl
"""

import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor


def main() -> None:
    binary, path = sys.argv[1], sys.argv[2]
    cases = [json.loads(line) for line in open(path, encoding="utf-8")]
    cwd = tempfile.mkdtemp()  # run from somewhere else: fonts must be built in

    def run(case):
        try:
            p = subprocess.run([binary, *case["args"]], capture_output=True, timeout=5, cwd=cwd)
            return p.stdout.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return "<timeout>"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outs = list(pool.map(run, cases))
    wrong = [(c, o) for c, o in zip(cases, outs) if o != c["out"]]
    print(f"{len(cases) - len(wrong)}/{len(cases)} cases match")
    for c, o in wrong[:5]:
        print("=" * 70)
        print("args:", c["args"])
        print("--- expected:")
        print(c["out"], end="")
        print("--- actual:")
        print(o, end="")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
