# Hardening Report

## 1. Holes closed

During Day 4 adversarial testing, cheat solutions were evaluated against the task in Harbor without implementing a full, correct Go port. These attacks exploited structural check weighting (`build` and `no_python` providing a 33.33% baseline) and partial heuristics:

- **Cheat 1 (Half-Port / Naive Capitalization Attack):**
  - **Job Folder:** `attack/cheat1-test/jobs/2026-11-18__17-25-19` (Trial ID: `cheat3-test__dtX27E7`)
  - **Score:** Overall reward **`0.3977`** (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.0965 / 9.65%)
  - *(Reference baseline:* `attack/empty-program-test/jobs/2026-11-18__16-59-22` scored `0.3333` with zero behaviour points, confirming the 33.33% structural check floor.*)*
  - **Vulnerability & Fix:** Implemented `simpleTitle()` in `attack/cheat1/solve.sh`, capitalizing the first character of whitespace-delimited words and lowercasing the rest. It passed structural checks and matched simple synthetic titles. During hardening, the old 2,000-input exam was replaced with the 100,000-input frozen exam (`tests/data/inputs.txt` and `tests/data/answers.txt`), reducing naive capitalization matching to near zero across comprehensive edge cases.

- **Cheat 2 (Enhanced Small-Word Heuristic):**
  - **Job Folder:** `attack/cheat2-test/jobs/2026-11-19__10-31-49` (Trial ID: `cheat4-test__RqjzYh3`)
  - **Score:** Overall reward **`0.4347`** (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.1520 / 15.20%)
  - **Vulnerability & Fix:** Added standard New York Times lowercase small-words filtering in `attack/cheat2/solve.sh`, improving matching on basic multi-word titles. During hardening, the 100K exam included small words at line boundaries, following sub-phrase punctuation, in hyphenated/slash compounds, and within quotes, defeating naive small-word lookup maps.

- **Cheat 3 (Punctuation-Aware Heuristic):**
  - **Job Folder:** `attack/cheat3-test/jobs/2026-11-19__10-49-21` (Trial ID: `cheat5-test__dqGUTrk`)
  - **Score:** Overall reward **`0.5177`** (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.2765 / 27.65%)
  - **Vulnerability & Fix:** Added heuristics in `attack/cheat3/solve.sh` for sub-phrase punctuation (`:`, `;`, `.`, `?`, `!`, `-`), hyphens, and apostrophe contractions (`O'`, `l'`, `d'`), pushing the composite reward past 50%. During hardening, the 100K exam challenged subtle rules (honorifics, initials `A.B.C`, `Mc/Mac`, inline periods, underscore boundaries, all-caps acronyms, and Unicode) that cannot be approximated with shallow rules.

- **Oracle Result:**
  - Evaluated on the frozen 100,000-title exam generated WITHOUT `regex` (standard library `re`, verified in `key/report.txt`), the Go Oracle port initially had **857 mismatches** out of 100,000 (99.143% accuracy, recorded in `measure/my-oracle.txt`).
  - The root cause was identified in `measure/oracle_mismatch_report.md`: `capFirst()` skipped leading underscores as punctuation (`_winter` $\rightarrow$ `_Winter`), whereas Python's `re` non-greedily matches `_` as `\w` and leaves following letters in lowercase.
  - After applying the minimal fix (`&& rs[i] != '_'`), the hardened Oracle achieved **0 wrong answers out of 100,000** (**100.0% accuracy**, recorded in `measure/my-oracle-after.txt`).

---

## 2. Exam: before and after

The **old exam** consisted of 2,000 synthetic titles (`attack/target/tests/data/hidden_inputs.txt`). An audit reveals it contained **zero** inputs with leading underscores (`_word`) and **zero** version strings (`v1.2`). Because these edge cases were completely absent, defective ports scored 1.0 without detection.

The **new exam** comprises **100,000 inputs** generated deterministically from seed `1` (`pool.txt`) and frozen strictly **WITHOUT regex** (using standard library `re`, `regex module used: False` in `key/report.txt`). Generated twice independently and verified via SHA-256 hashes, all 100,000 titles were retained with 0 dropped (100% stability), thoroughly exercising leading underscores, punctuation boundaries, version strings, and Unicode characters.

### Comparison Table

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
| :--- | :---: | :---: | :---: |
| **My Oracle (before hardening)** | 857 | No | ~0% ($3.4 \times 10^{-8}$) |
| **My Oracle (after hardening)** | 0 | n/a | n/a |
| **Aman Tiwari (`ports/aman-tiwari`)** | 0 | n/a | n/a |
| **Hardika (`ports/hardika`)** | 3,053 | No | ~0% ($1.8 \times 10^{-27}$) |

### Mathematical Justification of Probabilities:
- **My Oracle (before hardening, 857 errors):**  
  The probability that a random 2,000-title sample from the 100,000 pool misses all 857 defective titles is given by the hypergeometric distribution evaluated in `kit/compare.py`:  
  $$\text{Chance} = \frac{\binom{100000 - 857}{2000}}{\binom{100000}{2000}} \approx \left(1 - \frac{857}{100000}\right)^{2000} \approx 3.42 \times 10^{-8} \quad (\approx 0.0000034\%)$$  
  `kit/compare.py` formats this as `0%`. The old 2K exam missed it not due to random chance, but because its synthetic pool completely lacked leading underscores.
- **Hardika (3,053 errors):**  
  $$\text{Chance} = \frac{\binom{100000 - 3053}{2000}}{\binom{100000}{2000}} \approx \left(1 - \frac{3053}{100000}\right)^{2000} \approx 1.83 \times 10^{-27} \quad (\approx 0\%)$$  
  Hardika's 3,053 errors represent mode divergence: Hardika implemented Python `titlecase` WITH the `regex` module (which capitalizes `v1.2` $\rightarrow$ `V1.2`), whereas the reference exam was frozen WITHOUT `regex` (standard `re`, leaving `v1.2` lowercase). The old 2K exam contained no version strings and thus missed the divergence entirely.
- **Hardened Oracle & Aman Tiwari (0 errors):**  
  Because both ports achieve 0 errors across all 100,000 titles, there are no defective inputs in the population to detect; hence "Old exam caught it?" and the defect-miss probability are strictly **`n/a`** (in `kit/compare.py`, $\binom{100000}{2000} / \binom{100000}{2000} = 1.0 = 100\%$ indicates a 100% chance of observing zero defects).

---

## 3. What I learned

1. Input variety and adversarial edge cases expose bugs that high-volume standard inputs completely overlook.
2. Large exam scale (100,000 titles) is essential to eliminate the high miss probability of smaller test suites on rare bugs.
3. Reference specifications must explicitly declare library modes, as standard `re` and `regex` diverge on thousands of inputs.
