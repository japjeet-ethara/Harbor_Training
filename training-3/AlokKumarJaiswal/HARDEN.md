# Hardening Report: Practice 1 — titlecase-go

- **Target Task:** `alokinethara/titlecase-go`
- **Published Baseline:** `c48ed26`
- **Local Hardened Task Commit:** `a9e4b2c`

---

## Grader changes

In the published baseline (`c48ed26`), test grading computed an arithmetic weighted mean across checks:
```bash
($build_score * 1 + $no_python_score * 1 + $behaviour_score * 4) / 6
```
This structure allowed submissions that failed behaviour completely or only implemented basic structural checks to receive unearned credit (up to `0.333333` even with zero behaviour score). Furthermore, intermediate rounding obscured precision.

The hardened verifier (implemented in commit `34c21ed` and refined in commit `7d97189`) introduces a strict scoring gate:
1. **Strict Gating:** The verifier awards exact, unrounded behaviour credit only when both `build` and `no_python` pass (each scoring `1.0`). If either structural check fails, the final reward is strictly `0.0`.
2. **Exact Unrounded Precision:** The verifier extracts the exact, unrounded `raw` floating-point value from `criteria.hidden_output_matches` under the behaviour component, avoiding premature rounding to four decimal places.
3. **Diagnostic Retention:** Ungated diagnostic scores and full component breakdowns are retained in `/logs/verifier/reward-details.json`, while the authoritative gated reward is written to `/logs/verifier/reward.json`.

### Verification Run: `practice1-gated-partial-20261119-110602`
This behavior was confirmed in control job `practice1-gated-partial-20261119-110602`:
- **RewardKit Ungated Diagnostic Aggregate:** `0.4333` (the weighted mean of `build: 1.0`, `no_python: 1.0`, and `behaviour: 0.15`).
- **Final Gated Reward:** `0.15` (authoritative score reflecting exact behaviour correctness under the gating rule).
Both values came from the same run, demonstrating that structural passes no longer inflate partial behaviour scores.

---

## Exam before and after

### Test Suite Evolution
- **Original 2K Exam:** Consisted of 2,000 titles from `tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt` in baseline `c48ed26`. The measured comparison used those files.
- **Official 100K Exam:** Scaled to 100,000 unique titles generated using seed 1, Python 3.14.10, and standard-library `re`. Two independent reference runs agreed on every answer byte-for-byte, so zero titles were dropped (100,000 kept out of 100,000 generated). LF normalization was applied to Windows output to ensure strictly POSIX line endings.
- **Coverage vs. Size Confounding:** The expanded corpus exposed Unicode cases the original exam missed. Both exam size and input coverage changed, so the comparison doesn’t isolate the effect of size.
- **Verified Trainer Kit:** The generation and comparison scripts under [kit/](kit/) (`make_pool.py`, `answers.py`, `compare.py`) are identified as the verified trainer kit.

### Measurement Summary
Measurements across both exams are recorded in the three files under [measure/](measure/):

| Port | Original 2K wrong | Official 100K wrong | Estimated probability a random 2K sample misses every error |
| :--- | :--- | :--- | :--- |
| Final oracle | 0 | 0 | 1.0 (zero errors to find) |
| Lokesh | 0 | 3,069 | 4.433372440645427e-28 |
| Sanyam | 0 | 3,053 | 6.188645138595579e-28 |

The trainer comparator agreed with all three official wrong counts and displayed both tiny classmate probabilities as 0% after rounding. Both exams use re. Sanyam’s task used regex, and the cause of his differences was not isolated.

Detailed port evaluations:
- [measure/my-oracle.txt](measure/my-oracle.txt): Evaluates our measured oracle (`a9e4b2c`).
  - *Original 2K exam:* 2,000 titles, 0 wrong, sample size 2,000, miss probability 1.0.
  - *Official 100K exam:* 100,000 titles, 0 wrong, sample size 2,000, miss probability 1.0 (zero errors to find).
- [measure/LokeshDeshwal.txt](measure/LokeshDeshwal.txt): Evaluates classmate Lokesh Deshwal's published port from snapshot `01d11b155117f1e8bd9e842c4a943789ca3bed0d`.
  - *Original 2K exam:* 2,000 titles, 0 wrong, sample size 2,000, miss probability 1.0.
  - *Official 100K exam:* 100,000 titles, 3,069 wrong, sample size 2,000, miss probability 4.433372440645427e-28.
- [measure/SanyamSehrawat.txt](measure/SanyamSehrawat.txt): Evaluates classmate Sanyam Sehrawat's published port from snapshot `01d11b155117f1e8bd9e842c4a943789ca3bed0d`.
  - *Original 2K exam:* 2,000 titles, 0 wrong, sample size 2,000, miss probability 1.0.
  - *Official 100K exam:* 100,000 titles, 3,053 wrong, sample size 2,000, miss probability 6.188645138595579e-28.

### Oracle Defect Detection and Patching
Testing on the 100K exam suites revealed defects in the pre-fix oracle that passed unnoticed on the original 2K exam:
- **Local-Draft vs. Official Exam Discrepancies:**
  - *Original 2K exam:* Passed with 0 wrong (reward 1.0).
  - *Local-Draft 100K exam result:* Initial Harbor reward was `0.9202` in draft job `practice1-draft-100k-oracle-20261119-115454`, whereas the exact reward was `0.92024` in draft job `practice1-draft-100k-precise-20261119-121153`. The earlier **7,976 mismatches** are labeled as a local-draft result.
  - *Official 100K exam result:* Separately, on the official 100K exam, the oracle had **11,188 mismatches** before the thin-space fix and **zero afterward**.
- **Defects and Fixes:**
  1. *Non-breaking spaces (`\u00a0`) and Unicode words:* Python standard-library `re` treats `\u00a0` as whitespace under `\s` and recognizes Unicode letters and numbers under `\w`. The pre-fix Go port only recognized ASCII whitespace and ASCII word characters. Commit `d5be18e` patched `isSpace` to include `\u00a0` and `isWord` to recognize Unicode letters and numbers.
  2. *Turkish Dotted-I Casing (`\u0130`):* Python's `str.lower()` on `\u0130` produces `i\u0307` (`i` + combining dot above `\u0307`), which standard Go casing did not replicate. Commit `9020c42` added `pyLower` and adjusted `foldSmall` to correctly handle `\u0130` and `\u0131`.
  3. *Thin Spaces (`\u2009`):* The official 100K exam corpus included Unicode thin spaces (`\u2009`), which Python standard-library `re` treats as whitespace under `\s`. Before adding `\u2009` to `isSpace`, the oracle had 11,188 mismatches on the official exam; adding `\u2009` to `isSpace` resulted in zero mismatches afterward.
  4. *Sharp-S Handling (U+00DF):* `isAllCaps` treats U+00DF as lowercase, and `pyUpperRune` expands it to `SS` in both the first-character and apostrophe-second paths. This fix was verified with separate public probes.
- **Patched Oracle:** With these fixes applied, the patched oracle (`a9e4b2c`) achieved **zero wrong** on the official 100K exam.

### Integrated Harbor Controls
Hardened task integration was verified through final Harbor control runs:
- **Oracle Control:** Achieved `1.0` overall reward in job `practice1-official-100k-oracle-20261119-180231`.
- **Nop Control:** Achieved `0.0` overall reward in job `practice1-official-100k-nop-20261119-180431`.

---

## What I learned

1. **Small Exams Mask Edge Cases:** A 2,000-sample test suite was insufficient to detect subtle Unicode edge cases, allowing an oracle with flawed whitespace and casing handling to achieve a misleading 100% score. Expanding the exam to 100,000 titles exposed failure modes (7,976 mismatches in the local-draft result and 11,188 mismatches on the official exam before the thin-space fix) because the larger corpus introduced Unicode whitespace and character combinations that the original exam omitted.
2. **Library-Specific Semantics Matter:** Python's standard-library `re` behaves differently from external regex modules (e.g., `regex`) and other languages' regex engines (e.g., Go's `regexp`), especially regarding Unicode character classes (`\s` including non-breaking spaces `\u00a0` and thin spaces `\u2009`), case transformations (`\u0130` casing), and uppercase checks (U+00DF in `isAllCaps`). Ports must strictly match the exact contract of the target library.
3. **Scoring Gates Prevent Score Inflation:** Arithmetic averaging in multi-criteria evaluation allows broken submissions to gain artificial credit from simple structural checks. Gating behaviour scores behind mandatory build and hygiene gates ensures that reward strictly reflects functional correctness.
4. **Preserving Full Precision is Essential:** Premature rounding in grading scripts discards discriminative capability. Operating on raw unrounded values maintains precision across large exam datasets.

---

## Pending verification

We measured Sanyam’s published Practice 1 port on both exams. It had 3,053 wrong on the official 100K exam in re mode. His Day 4 report and submissions against our task have not been evaluated. Verification that each submission scores below 0.2 remains pending.
