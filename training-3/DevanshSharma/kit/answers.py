"""answers.py <python-titlecase-dir> <pool.txt> <out_dir>

Run the ORIGINAL python-titlecase (stdlib re, no regex package) over every
line in pool.txt TWICE.  Keep only the lines whose answer is identical both
times (stability check).  Write:
  <out_dir>/inputs.txt    — kept input lines
  <out_dir>/answers.txt   — corresponding answers
  <out_dir>/report.txt    — how many kept / dropped / which mode

Run with: python -I answers.py <dir> pool.txt key
"""
import sys
from pathlib import Path

TC_DIR  = Path(sys.argv[1])
POOL    = Path(sys.argv[2])
OUT_DIR = Path(sys.argv[3])

sys.path.insert(0, str(TC_DIR))

# Block the 'regex' package so titlecase falls through to `import re as regex`.
# We install a meta path finder that raises ImportError for 'regex'.
import importlib.abc, importlib.machinery

class _BlockRegex(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "regex":
            raise ImportError("regex blocked by answers.py")
        return None

sys.meta_path.insert(0, _BlockRegex())
# Also remove any cached copy
sys.modules.pop("regex", None)

from titlecase import titlecase  # noqa: E402

pool_lines = Path(POOL).read_text(encoding="utf-8").splitlines()

run1 = [titlecase(l) for l in pool_lines]
run2 = [titlecase(l) for l in pool_lines]

kept_in, kept_ans = [], []
dropped = 0
for orig, a1, a2 in zip(pool_lines, run1, run2):
    if a1 == a2:
        kept_in.append(orig)
        kept_ans.append(a1)
    else:
        dropped += 1

OUT_DIR = Path(OUT_DIR)
OUT_DIR.mkdir(parents=True, exist_ok=True)
Path(OUT_DIR / "inputs.txt").write_text("\n".join(kept_in) + "\n",  encoding="utf-8", newline="\n")
Path(OUT_DIR / "answers.txt").write_text("\n".join(kept_ans) + "\n", encoding="utf-8", newline="\n")

mode_note = "stdlib re (no regex package)"
report = (
    f"pool:    {len(pool_lines)}\n"
    f"kept:    {len(kept_in)}\n"
    f"dropped: {dropped}\n"
    f"mode:    {mode_note}\n"
)
Path(OUT_DIR / "report.txt").write_text(report, encoding="utf-8")
print(report, end="")
