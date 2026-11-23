# Day 5 Hardening Report

**Author:** Abhishek Nain  
**Task:** `training-3/AbhishekNain/task/` (`titlecase-go`)  

---

## 1. Frozen 100,000-Title Corpus & Reference Baseline

I generated a frozen 100,000-title corpus to test behaviour beyond the 76 legacy tests, using `kit/make_pool.py` with count `100000` and seed `1`.

Answers were frozen using the upstream Python reference package:
- **Reference Repository:** `python-titlecase` pinned at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- **Runtime Environment:** Python `3.14.10`
- **Regex Engine:** `regex` package version `2026.11.19` (compiled with `regex` module enabled)

The trainer kit produced identical answers across two isolated Python runs (Python's `-I` isolated mode ignores `PYTHONHASHSEED`). Across all 100,000 generated titles, both runs produced identical answers with zero drops:
- **Pool Inputs:** 100,000
- **Kept (Stable):** 100,000
- **Dropped (Unstable):** 0
- **Regex Module Used:** `True`

The complete freeze summary is recorded in [`kit/report.txt`](kit/report.txt). The stable inputs and answers were saved as frozen test fixtures in `task/tests/data/inputs.txt` and `task/tests/data/answers.txt`.

---

## 2. Go Port Vulnerability & Trailing Small-Word Fix

When evaluating my original Go implementation against the 100,000-title corpus, I identified a systematic trailing small-word matching bug in `applySmallLast` and `matchAltEnding`.

### The Bug
In the reference implementation, `SMALL_LAST = regex.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), regex.I)` matches a small word preceded by a word boundary (`\b`) and optionally followed by trailing punctuation.

In the Go port, `smallAlts` lists small words in alphabetical order, placing `"a"` before `"via"`. For any trailing word ending in `"via"` (e.g., `"sent via"` or `"via-"`):
1. `matchAltEnding` checked candidates without validating the leading word boundary during candidate selection.
2. Because `"via"` ends in `"a"`, `"a"` matched the suffix first, returning `start = 2`.
3. `applySmallLast` received `start = 2`, checked `isBoundary(rs, 2)` (between `'i'` and `'a'`), found it was not a word boundary, and rejected the candidate.
4. Because `matchAltEnding` had already returned, the search halted without ever attempting `"via"`, leaving trailing `"via"` uncapitalized.

### The Fix
I updated `matchAltEnding` to check `isBoundary(rs, start)` directly as part of candidate selection:
- An invalid suffix match (such as `"a"` inside `"via"`) fails the boundary test and does not terminate candidate search.
- The loop continues and selects `"via"` at index `0` (where `isBoundary(rs, 0)` holds).
- The existing evaluation order of `smallAlts` and punctuation handling (`isPunct(rs[len(rs)-1])`) remain completely intact.

### Measured Impact
On the 100,000-title corpus:
- The first five recorded mismatches in [`measure/my-oracle-before.txt`](measure/my-oracle-before.txt) involved trailing `via` (e.g., `McDonald Mrs\tvia`, `via via`, `via-`).
- The boundary candidate fix reduced the total number of mismatches from 1,045 to zero, as documented in [`measure/my-oracle.txt`](measure/my-oracle.txt).

---

## 3. Harbor Verification Results

I verified the task using Harbor across both unchanged baseline and hardened runs:

| Job Name | Description | Test Results | Reward |
| :--- | :--- | :--- | :--- |
| `abhishek-day5-baseline-oracle-05` | Unchanged baseline oracle | Legacy tests passed | `1.0` |
| `abhishek-day5-baseline-nop-01` | Unchanged baseline no-op | Legacy tests failed | `0.0` |
| `abhishek-day5-100k-oracle-01` | Original oracle against legacy tests + 100k corpus test | 76 passed, 1 failed (failed corpus test) | `0.0` |
| `abhishek-day5-100k-oracle-02` | Fixed oracle against legacy tests + 100k corpus test | 77 passed, 0 failed | `1.0` |
| `abhishek-day5-100k-nop-01` | Hardened no-op baseline | 0 passed, 77 failed | `0.0` |

The original oracle passed all 76 legacy unit tests but failed the added 100k corpus test in `abhishek-day5-100k-oracle-01`. The fixed oracle passed all 77 tests and scored `1.0` in `abhishek-day5-100k-oracle-02`. The hardened no-op scored `0.0` in `abhishek-day5-100k-nop-01`.

---

## 4. Classmate Measurements & Peer Status

Using the frozen 100,000-title corpus and my legacy verifier suite, I evaluated classmate implementations alongside my own oracles. Both classmates’ legacy results were obtained via direct pytest runs in my original verifier Docker image (not generating Harbor rewards).

### Summary Comparison Table

| Implementation | Legacy Verifier (Abhishek's Tests) | 100k Corpus Mismatches | 2,000-Title Miss Probability | Source / Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **My original oracle** | 76/76 passed | 1,045 wrong of 100,000 | 0% | [`measure/my-oracle-before.txt`](measure/my-oracle-before.txt) |
| **My fixed oracle** | 76/76 passed | 0 wrong of 100,000 | N/A* | [`measure/my-oracle.txt`](measure/my-oracle.txt) |
| **Mukul Bhardwaj** | 5 passed, 71 failed | 2,221 wrong of 100,000 | 0% | [`measure/mukul.txt`](measure/mukul.txt) |
| **Devansh Kakwani** | 62 passed, 14 failed | 2,227 wrong of 100,000 | 0% | [`measure/devansh-kakwani.txt`](measure/devansh-kakwani.txt) |

*\*Note: For the fixed oracle, the comparator's 2,000-title miss probability is marked N/A because there were zero mismatches (the raw comparator prints 100% in this zero-error case).*

### Detailed Notes

- **My Original Oracle vs. Fixed Oracle:**  
  Both passed all 76 legacy tests. On the expanded 100,000-title corpus, the original oracle had 1,045 wrong answers (0% miss probability). The boundary candidate fix eliminated all errors, achieving 0 mismatches.
- **Mukul Bhardwaj (`measure/mukul.txt`):**  
  Mukul's submission had **2,221 mismatches** out of 100,000 titles, with `v1.2` as one observed example. The comparator rounded the 2,000-title miss probability to 0%. On my legacy verifier, his binary (tested from the unmodified `a2bca77` binary collected by Harbor job `mukul-baseline-a2bca77-oracle-01`) yielded 5 passed and 71 failed. However, because our tasks have different CLI and newline contracts, this failure count cannot be interpreted as 71 titlecasing errors.
- **Devansh Kakwani (`measure/devansh-kakwani.txt`):**  
  I built `devanshkakwani/main.go` and `go.mod` from commit `eabc3c385130cbec93612cb21df355d3e42f3d38`. On the expanded corpus, Devansh had **2,227 mismatches** out of 100,000 titles (0% miss probability). On my legacy verifier, Devansh had 62 passed and 14 failed: he passed all legacy titlecasing-rule tests, with the 14 failures confined to CLI, wordlist, and line handling.
- **Devansh's Day 4 Report & Submission Reruns:**  
  *Pending*. Devansh's Day 4 report was not located on the fetched branch, so his submissions have not been rerun and their scores remain pending.

---

## 5. Key Takeaways

1. **Legacy test blind spots:** My old tests missed the trailing small-word bug entirely, allowing 1,045 mismatches to pass undetected across all 76 legacy tests until the 100,000-title corpus caught them.
2. **Contract alignment:** Preserving regex mode in the reference generation kept the comparison strictly aligned with my task contract.
3. **Interpreting classmate results:** Classmate CLI failures on my legacy verifier need to be interpreted separately from batch titlecasing mismatches, as disparate CLI or newline contracts do not imply titlecasing rule errors.
