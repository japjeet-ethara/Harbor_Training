# 5-Minute Defence Talk Outline: Hardening titlecase-go

**Speaker:** Alok Kumar Jaiswal
**Task:** `titlecase-go`
**Duration:** 5 Minutes
**Final Local Task Revision:** `b1019a4`

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

### Slide / Topic: Gating and Squared Behaviour Scoring
1. **Strict Scoring Gate (`build` and `no_python` gate behaviour credit):**
   - Behaviour credit is now strictly conditional on passing both `build` and `no_python` gates (`1.0` each).
   - If either structural check fails, the final reward is strictly `0.0`. Passing compilation or having no Python files no longer awards unearned baseline points.
2. **Squared Behaviour Scoring & Unrounded Precision:**
   - In final task revision `b1019a4`, the verifier publishes the square of raw behaviour ($\text{reward} = \text{behaviour}^2$) when both structural checks pass, and zero otherwise.
   - Squaring changes the reward for partial correctness while preserving raw accuracy and the official exam.
   - Raw behaviour is extracted directly as an unrounded float from `criteria.hidden_output_matches`, preventing premature precision loss.

> **Speaking Notes:**
> - "To fix this, we implemented strict structural gating and squared behaviour scoring in final local task revision b1019a4."
> - "First: `build` and `no_python` strictly gate behaviour credit. If the binary fails to build or Python files are present, reward is zero—no free structural baseline."
> - "Second: when both structural checks pass, the verifier publishes the square of raw behaviour, and zero otherwise. Squaring changes the reward for partial correctness while preserving raw accuracy and the official exam."

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

### Slide / Topic: Verified Control Rewards and Classmate Audits
- **Verified Control Rewards (Task Revision `b1019a4`):**
  - Final Oracle Reward: `1.0` in job `practice1-squared-oracle-20261120-125015` (verified in [proof/oracle-reward.json](proof/oracle-reward.json)).
  - Nop Baseline Reward: `0.0` in job `practice1-squared-nop-20261120-125222` (verified in [proof/nop-reward.json](proof/nop-reward.json)).
- **Classmate Submission Results:**
  - Baseline rewards are attributed to Sanyam’s published report.
  - Sanyam Cheat 2 first scored `0.33993` under the linear gate in `practice1-sanyam-cheat2-hardened-20261120-124059`. It fell below 0.2 after squaring ($0.33993^2 = 0.1155524049$).
  - Sanyam independently replayed all three submissions on published revision `395755d`. All three scored below `0.2`. [Independent retest](https://github.com/japjeet-ethara/Harbor_Training/blob/c40906d0a797c025b5e63df5b7a63538640fb926/training-3/SanyamSehrawat/attack/ATTACK.md#10-day-6--independent-re-attack-on-aloks-hardened-task)

### Verified Results Summary

| Check | Baseline reward | Final reward | Final Harbor job |
| :--- | :--- | :--- | :--- |
| **Sanyam Cheat 1** | 0.3640 | 0.0001890625 | `practice1-sanyam-cheat1-squared-20261120-125733` |
| **Sanyam Cheat 2** | 0.5217 | 0.1155524049 | `practice1-sanyam-cheat2-squared-20261120-124826` |
| **Sanyam Cheat 3** | 0.3640 | 0.0001879641 | `sanyam-day6-cheat3-395755d` |
| **Separate echo-only control** | — | 0.0001879641 | `practice1-echo-only-squared-20261120-130327` |

*Proof Artifacts:* Linked in [proof/cheats-reward.txt](proof/cheats-reward.txt), [proof/sanyam-cheat1-reward.json](proof/sanyam-cheat1-reward.json), [proof/sanyam-cheat2-reward.json](proof/sanyam-cheat2-reward.json), [proof/sanyam-cheat3-reward.json](proof/sanyam-cheat3-reward.json), and [proof/echo-only-reward.json](proof/echo-only-reward.json).

> **Speaking Notes:**
> - "Verified Control Rewards under final revision b1019a4: the runs confirmed oracle 1.0 in `practice1-squared-oracle-20261120-125015` and nop 0.0 in `practice1-squared-nop-20261120-125222`."
> - "Evaluating Sanyam's Day 4 attacks: Cheat 1 earned 0.0001890625. Cheat 2, which initially scored 0.33993 under the linear gate, dropped to 0.1155524049 after squaring, safely below 0.2."
> - "The independent Cheat 3 replay scored 0.0001879641, matching our earlier echo-only control."
> - "All three independent retests scored below 0.2 on published revision 395755d."
