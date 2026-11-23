# Hardening Report

## 1. Holes closed

During Day 4 adversarial testing, cheat solutions were evaluated against the task in Harbor without implementing a full, correct Go port. These attacks exploited structural check weighting (`build` and `no_python` providing a 33.33% baseline) and partial heuristics.

During Day 5 hardening, we re-weighted the criteria (`reward.toml` weights: `build: 1.0, no_python: 1.0, behaviour: 23.0`), added a canonical specification smoke test to `no_python.py`, and deployed the 100,000 frozen exam.

### Summary: Before and After Hardening

| Cheat Solution | Old Score (Day 4) | Old Job Folder | Hardened Score (Day 5/6) | Hardened Job Folder | Result |
| :--- | :---: | :--- | :---: | :--- | :---: |
| **Cheat 1 (Half-Port Heuristic)** | `0.3977` | `attack/cheat1-test/jobs/2026-11-18__17-25-19` | **`0.1355`** | `jobs/2026-11-21__23-55-01` | **PASSED (< 0.20)** |
| **Cheat 2 (Small-Word Heuristic)** | `0.4347` | `attack/cheat2-test/jobs/2026-11-19__10-31-49` | **`0.1684`** | `jobs/2026-11-21__23-57-05` | **PASSED (< 0.20)** |
| **Cheat 3 (Punctuation Heuristic)** | `0.5177` | `attack/cheat3-test/jobs/2026-11-19__10-49-21` | **`0.2205`** | `jobs/2026-11-21__23-59-05` | **DEFENDED** |

*(Note: Against classmate Arun's task with an 80% behavior gate, Cheats 1, 2, and 3 all score **`0.0000`**; see `attack/ATTACK.md`).*

---

### Detailed Breakdown

- **Cheat 1 (Half-Port / Naive Capitalization Attack):**
  - **Was:** `0.3977` (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.0965 / 9.65%) in job `attack/cheat1-test/jobs/2026-11-18__17-25-19`.
  - **Now:** **`0.1355`** (`build`: 1.0, `no_python`: 0.0, `behaviour`: 0.10382) in job `jobs/2026-11-21__23-55-01`.
  - *(Reference baseline:* `attack/empty-program-test/jobs/2026-11-18__16-59-22` scored `0.3333` with zero behaviour points, confirming the 33.33% structural check floor.*)*
  - **Vulnerability & Fix:** Implemented `simpleTitle()` in `attack/cheat1/solve.sh`, capitalizing the first character of whitespace-delimited words and lowercasing the rest. During hardening:
    1. Added a canonical specification smoke test to `task/tests/no_python.py`, which caused Cheat 1's `no_python` score to drop from `1.0` to `0.0`.
    2. Re-weighted `task/tests/reward.toml` to `{build: 1.0, no_python: 1.0, behaviour: 23.0}`, capping the maximum possible structural reward at $4.0\%$ ($1.0/25.0$) for a build-only pass.
    3. Replaced the 2,000-input exam with the 100,000 frozen exam (`tests/data/inputs.txt`), bringing total reward down to **`0.1355`** ($< 0.20$).

- **Cheat 2 (Enhanced Small-Word Heuristic):**
  - **Was:** `0.4347` (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.1520 / 15.20%) in job `attack/cheat2-test/jobs/2026-11-19__10-31-49`.
  - **Now:** **`0.1684`** (`build`: 1.0, `no_python`: 0.0, `behaviour`: 0.13959) in job `jobs/2026-11-21__23-57-05`.
  - **Vulnerability & Fix:** Added standard New York Times lowercase small-words filtering in `attack/cheat2/solve.sh`. During hardening:
    1. Caught by the `no_python.py` smoke test (`no_python` dropped to `0.0`).
    2. The 100K exam included small words at line boundaries, following sub-phrase punctuation, in hyphenated/slash compounds, and within quotes, reducing reward to **`0.1684`** ($< 0.20$).

- **Cheat 3 (Punctuation-Aware Heuristic):**
  - **Was:** `0.5177` (`build`: 1.0, `no_python`: 1.0, `behaviour`: 0.2765 / 27.65%) in job `attack/cheat3-test/jobs/2026-11-19__10-49-21`.
  - **Now:** **`0.2205`** (`build`: 1.0, `no_python`: 0.0, `behaviour`: 0.19617) in job `jobs/2026-11-21__23-59-05`.
  - **Vulnerability & Fix:** Added heuristics for sub-phrase punctuation (`:`, `;`, `.`, `?`, `!`, `-`), hyphens, and apostrophe contractions (`O'`, `l'`, `d'`). During hardening:
    1. Structural exploit closed: `no_python` dropped from `1.0` to `0.0`. The only structural credit Cheat 3 receives is compilation (`build: 1.0`), which contributes only $1.0/25.0 = 0.0400$ ($4.0\%$).
    2. On the 100K exam, Cheat 3 achieves genuine exact line matches on 19,617 titles ($19.62\% \times 23.0/25.0 = 0.1805$).
    3. Total reward dropped from `0.5177` to **`0.2205`** (a 57.4% reduction). Per `instruction.md` Section 6, the task honors honest partial credit without artificial cliffs. (Documented and defended in `DEFENCE.md`).

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
