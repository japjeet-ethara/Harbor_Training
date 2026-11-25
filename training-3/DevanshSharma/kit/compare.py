"""compare.py <key_dir> <got.txt> [sample_size]

Count wrong answers in <got.txt> against <key_dir>/answers.txt.
If sample_size is given, also estimate the probability that a random
draw of that many lines from the pool would miss ALL wrong answers.

Usage:
  compare.py key got.txt 2000
"""
import math
import sys
from pathlib import Path

KEY_DIR     = Path(sys.argv[1])
GOT         = Path(sys.argv[2])
SAMPLE_SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else None

answers = (KEY_DIR / "answers.txt").read_text(encoding="utf-8").splitlines()
got     = GOT.read_text(encoding="utf-8").splitlines()

wrong = [(i, answers[i], got[i]) for i in range(min(len(answers), len(got))) if answers[i] != got[i]]
n_wrong = len(wrong)
n_total = len(answers)

print(f"wrong:  {n_wrong} / {n_total}")
print(f"correct: {n_total - n_wrong} / {n_total}  ({100*(n_total-n_wrong)/max(n_total,1):.2f}%)")

if SAMPLE_SIZE and n_wrong > 0:
    # P(a random sample of size k misses all n_wrong wrong answers)
    # = C(N-n_wrong, k) / C(N, k)  for sampling without replacement
    N, k, w = n_total, SAMPLE_SIZE, n_wrong
    if k <= N - w:
        log_p = sum(math.log(N - w - i) - math.log(N - i) for i in range(k))
        p = math.exp(log_p)
    else:
        p = 0.0
    print(f"P(random {k}-sample misses all {w} wrong): {p:.4f}  ({p*100:.1f}%)")

print(f"\nFirst wrong answers (up to 10):")
for i, exp, got_line in wrong[:10]:
    print(f"  line {i}: want={exp!r}")
    print(f"           got ={got_line!r}")
