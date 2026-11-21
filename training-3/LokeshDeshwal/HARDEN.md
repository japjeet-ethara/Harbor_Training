# Hardening Report: titlecase-go Task

Author: Lokesh Deshwal
Task: `practice/titlecase-go`
Date: 2026-11-20

---

## Holes closed

### Cheat 1 (Compound-Word Control)
- **Before:** Reward `0.573000` (build: 1, no_python: 1, behaviour: 0.359500)
- **Now:** Reward `0.000000` (build: 0, no_python: 0, behaviour: 0.000000)
- **Fix:** Gated `build` and `no_python` credit so they are only awarded when behaviour achieves $\ge 98\%$ accuracy. Tested compound words across 100,000 inputs alongside complex punctuation combinations and URL exceptions.

### Cheat 2 (Capitalization with Interior Small Words)
- **Before:** Reward `0.624000` (build: 1, no_python: 1, behaviour: 0.436000)
- **Now:** Reward `0.000000` (build: 0, no_python: 0, behaviour: 0.000000)
- **Fix:** Replaced linear partial credit with an accuracy gate (< 0.98 yields 0). Added 100,000 synthetic inputs covering edge cases (mixed case, subphrase punctuation, acronyms, and contractions) where naive small-word lookup fails.

### Cheat 3 (Combined Partial Port)
- **Before:** Reward `0.905333` (build: 1, no_python: 1, behaviour: 0.858000)
- **Now:** Reward `0.000000` (build: 0, no_python: 0, behaviour: 0.000000)
- **Fix:** Switched from `paste ... | awk -F'\t'` to a byte-exact streaming line comparator in Python (eliminating intra-line tab splitting gaps). Enforced a strict $\ge 0.98$ behaviour threshold so partial ports omitting URLs and edge-case grammar receive zero score.

---

## Exam: before and after

- **Old exam:** 2,000 inputs
- **New exam:** 100,000 inputs, mode: `re` (titlecase WITHOUT regex)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
| :--- | :--- | :--- | :--- |
| **my oracle** | 0 of 100,000 | n/a | n/a |
| **neha-gaur** | 3,520 of 100,000 | no (scored 1.0) | 0% |
| **saurabh-baghel** | 3,520 of 100,000 | no (scored 1.0) | 0% |

---

## What I learned (3 lines)

1. Small test sets give a false sense of security: ports that score 1.0 on 2,000 inputs fail thousands of times on edge cases like `v1.2`, Unicode letters, and apostrophe compounds.
2. Ungated structural checks (`build` + `no_python`) give away free points; grading must gate structural credit behind verified behavioral accuracy.
3. Text comparators must be byte-exact: simple tools like `paste` and `awk -F'\t'` break when inputs contain tabs or Unicode whitespace.
