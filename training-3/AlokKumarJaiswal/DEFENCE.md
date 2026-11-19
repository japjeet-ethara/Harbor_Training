# 5-Minute Defence Talk Outline: Hardening titlecase-go

**Speaker:** Alok Kumar Jaiswal  
**Task:** `titlecase-go`  
**Duration:** 5 Minutes  

---

## Minute 1: Day 4 Attack Recap & Strongest Result (0:00 – 1:00)

### Slide / Topic: Exploiting Structural Credit on Lokesh’s Pinned Task
- **Strongest Day 4 Result:** The combined partial port scored **0.905333** overall reward on Lokesh’s pinned task (`practice/titlecase-go`), with a reported behaviour score of **0.858000**.
- **Vulnerability Context:** Unhardened composite scoring awarded unearned structural credit (up to 0.333333 for `build` and `no_python`), allowing an incomplete implementation that handled small words, compounds, all-caps, and dotted initials—but omitted URL handling and other rules—where the incomplete port earned 90.53% overall reward.
- **Attack Reference:** Full methodology and submission measurements documented in [attack/ATTACK.md](attack/ATTACK.md).

> **Speaking Notes:**
> - "On Day 4, we evaluated vulnerabilities in Lokesh's pinned task using targeted partial implementations."
> - "Our strongest result was the combined partial port: the incomplete port earned 90.53% overall reward (0.905333) with a reported behaviour score of 0.858000, despite leaving major rules like URL exceptions completely unhandled."
> - "We measured this score directly; the assignment specifies no Day 4 passing threshold, but composite scoring clearly inflated partial implementations."

---

## Minute 2: Two Critical Grader Fixes (1:00 – 2:00)

### Slide / Topic: Gating and Precision Architecture
1. **Strict Scoring Gate (`build` and `no_python` gate behaviour credit):**
   - Behaviour credit is now strictly conditional on passing both `build` and `no_python` gates (`1.0` each).
   - If either structural check fails, the final reward is strictly `0.0`. Passing compilation or having no Python files no longer awards unearned baseline points.
2. **Unrounded Behaviour Scores:**
   - The verifier extracts exact, unrounded raw floating-point behaviour scores directly from `criteria.hidden_output_matches`.
   - Eliminates premature rounding to 4 or 6 decimal places, preserving precision across large exam corpora.

> **Speaking Notes:**
> - "To fix this, we implemented two major grader improvements."
> - "First: `build` and `no_python` now strictly gate behaviour credit. If the binary fails to build or Python files are present, reward is zero—no free structural baseline."
> - "Second: the verifier now publishes unrounded behaviour scores directly from raw output comparisons, preventing premature truncation."

---

## Minute 3: Exam Scaling: Before and After (2:00 – 3:00)

### Slide / Topic: 2K Original vs. 100K Official Exam Suite
- The official exam exposed differences the original exam missed. Both exam size and coverage changed.
- The original 2,000-sample exam masked edge cases, while the official 100,000-sample suite expanded character coverage under standard-library `re`.

### Before-and-After Exam Table

| Port | Original 2K Exam Wrong | Official 100K Exam Wrong |
| :--- | :---: | :---: |
| **Final Oracle** | 0 | 0 |
| **Lokesh** | 0 | 3,069 |
| **Sanyam** | 0 | 3,053 |

*Reference-Mode Note:* Sanyam's port used the `regex` module reference mode, whereas the official evaluation ran under standard-library `re`. We note this reference-mode difference without attributing his errors to it.

> **Speaking Notes:**
> - "The official exam exposed differences the original exam missed, as both exam size and coverage changed."
> - "On the original 2K exam, all three ports had exactly zero wrong—giving a misleading appearance of parity."
> - "On the official 100K exam, the final oracle had 0 wrong, while Lokesh had 3,069 wrong and Sanyam had 3,053 wrong."
> - "We note Sanyam's port used `regex` reference mode while our exam used `re`, but we do not attribute his errors to that mode difference."

---

## Minute 4: The Surprise — Unicode Thin Space (U+2009) (3:00 – 4:00)

### Slide / Topic: The 11,188 Mismatch Revelation
- **The Pre-Fix Failure:** On the official 100K exam, our pre-fix oracle initially produced **11,188 mismatches**.
- **The Surprise:** All 11,188 official-exam mismatches involved a single character: **U+2009 (Unicode thin space)**.
- **The Fix:** Python's standard-library `re` engine includes `U+2009` under whitespace `\s`. Adding `U+2009` to the Go whitespace splitter (`isSpace`) immediately reduced the wrong count from 11,188 to **0** on the exact same corpus.

> **Speaking Notes:**
> - "Here is the biggest surprise of our defence: all 11,188 official-exam mismatches in our draft oracle involved U+2009, the Unicode thin space."
> - "Python's standard `re` treats `\u2009` as whitespace in `\s`. Our Go port's splitter originally missed it."
> - "Once we added U+2009 to the whitespace splitter, the error count dropped from 11,188 to exactly zero on the same 100K dataset."

---

## Minute 5: Control Proofs & Verification Status (4:00 – 5:00)

### Slide / Topic: Verified Control Rewards and Pending Submissions
- **Verified Control Rewards:**
  - The runs confirmed oracle `1.0` and nop `0.0` on the hardened task.
  - Final Oracle Reward: `1.0` &rarr; verified in [proof/oracle-reward.json](proof/oracle-reward.json).
  - Nop Baseline Reward: `0.0` &rarr; verified in [proof/nop-reward.json](proof/nop-reward.json).
- **Classmate Submission Audits:**
  - Verification against Sanyam’s Day 4 submissions remains pending. His scores are left blank.

### Control & Audit Summary

| Target / Submission | Overall Reward | Verification Status |
| :--- | :---: | :--- |
| **Final Oracle** | 1.0 | Verified in [proof/oracle-reward.json](proof/oracle-reward.json) |
| **Nop Baseline** | 0.0 | Verified in [proof/nop-reward.json](proof/nop-reward.json) |
| **Sanyam Day 4 Submissions** | | *Pending verification* |

> **Speaking Notes:**
> - "Verified Control Rewards: the runs confirmed oracle 1.0 and nop 0.0 on the hardened task (verified in [proof/oracle-reward.json](proof/oracle-reward.json) and [proof/nop-reward.json](proof/nop-reward.json))."
> - "Verification against Sanyam's Day 4 submissions remains pending, so those scores remain blank."
> - "The official exam and both Harbor controls are verified. The remaining check is whether each of Sanyam’s Day 4 submissions scores below 0.2. Thank you."
