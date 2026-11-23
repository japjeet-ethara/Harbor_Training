# DEFENCE — Lokesh Deshwal (5-Minute Talk Notes & Security Proof)

Author: Lokesh Deshwal  
Task: `practice/titlecase-go`  
Attacker: Alok Kumar Jaiswal  
Date: 2026-11-20  
Harbor Version: 0.25.0  

---

## 1. The Strongest Cheat Against My Task

**Alok Kumar Jaiswal's Cheat 3 (Combined Partial Port):**
- **Before Hardening:** Scored **`0.905333`** (build: 1, no_python: 1, behaviour: 0.858000) in job `lokesh-practice1-combined-control-20261119-100151`.
- **After Hardening:** Scored **`0.000000`** in job `lokesh-day6-cheat3-20261120-155840`.

### Why it worked on the old task:
1. **Unearned Structural Credit:** The old rubric gave 1/6 for `build` and 1/6 for `no_python`, injecting an automatic $0.333333$ baseline reward for compiling an empty program.
2. **Ungated Partial Behaviour:** The verifier awarded linear partial credit without an accuracy threshold, allowing an incomplete port that skipped URL handling, acronyms, and edge cases to score over $90\%$.
3. **Tab-Delimited Comparator Flaw:** The verifier used `paste ... | awk -F'\t'`, which breaks and misaligns when inputs contain intra-line tab characters or Unicode whitespace.

### How I closed the holes:
1. **Strict Accuracy Gate:** Implemented a non-linear threshold where any submission with $< 98\%$ behavioural accuracy receives `0.0` behaviour reward.
2. **Gated Structural Points:** `build` and `no_python` credit are only awarded if behavioural accuracy achieves $\ge 98\%$.
3. **Byte-Exact Streaming Comparator:** Replaced shell parsing with a streaming Python comparator that verifies line-by-line byte identity and enforces exact line count matching.
4. **Candidate Process Isolation & Exit Code Verification:** The verifier enforces that the candidate binary exits cleanly with exit code `0`. Any crash, timeout, or partial output yields `0.0`.
5. **Addressed Attacker Review:** In response to Alok's Day 6 static review note, `test.sh` explicitly verifies both candidate process exit status (`exit 0`) and exact line count match ($100,000$ lines), preventing truncated-output exploits.

---

## 2. Exam Before and After

- **Old Exam:** 2,000 synthetic inputs.
- **New Exam:** 100,000 inputs generated via `kit/make_pool.py 100000 1`, answered in standard `re` mode (**titlecase WITHOUT regex**). Answers frozen twice with 0 dropped entries. Specified in `instruction.md`.

| Port | Wrong on 100K Exam | Old Exam Caught It? | Chance 2K Random Misses It | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **my oracle (hardened)** | **0 of 100,000** | n/a | n/a | 100% exact match (`measure/my-oracle.txt`) |
| my oracle (original) | 3,520 of 100,000 | No (scored 1.0) | 0% | Missed 3 edge cases (now fixed) |
| **Neha Gaur** | 3,520 of 100,000 | No (scored 1.0) | 0% | Identical baseline flaws (`measure/neha-gaur.txt`) |
| **Saurabh Baghel** | 3,520 of 100,000 | No (scored 1.0) | 0% | Identical baseline flaws (`measure/saurabh-baghel.txt`) |

---

## 3. What Surprised Me (3 Bugs Found in Oracle)

The 100,000-input exam exposed **three genuine bugs in my own Go oracle** that the 2,000-input exam failed to detect:

1. **Inline Version Decimal Preservation (`v1.2`):**  
   - In Python, version strings like `v1.2` remain lowercase.  
   - My original regex capitalized it to `V1.2`.  
   - *Fix:* Updated `inlinePeriodRegex` to `[\p{L}0-9_]\.[\p{L}0-9_]`.
2. **Leading Underscores (`_dream`):**  
   - Python's `CAPFIRST = ^[PUNCT]*?([\w])` is lazy, and `_` is both punctuation and word character, leaving `_dream` lowercase.  
   - My port originally capitalized it to `_Dream`.  
   - *Fix:* Adjusted prefix handling in `capfirstRegex`.
3. **Dot Loss in Single-Letter Initialisms (`v._`):**  
   - `smallFirstRegex.ReplaceAllStringFunc` passed matched substring `"v."` to callback without trailing punctuation, stripping the dot.  
   - *Fix:* Replaced callback with `FindStringSubmatchIndex` on `tcLine[0]`.

After fixing these 3 bugs, my Go oracle achieved **0 wrong answers out of 100,000** (100.00% exact match).

---

## 4. Official Harbor Verification Proofs

All runs executed under Harbor 0.25.0:

| Submission / Control | Required Score | Observed Score | Job ID / Evidence |
| :--- | :---: | :---: | :--- |
| **Published Oracle** | `1.000` | **`1.000000`** | `proof/oracle-reward.json` (Job `2026-11-20__17-40-28`) |
| **Nop Baseline** | `0.000` | **`0.000000`** | `proof/nop-reward.json` (Job `2026-11-20__17-39-17`) |
| **Cheat 1 (Compound words)** | `< 0.20` | **`0.000000`** | `proof/cheats-reward.txt` (Job `lokesh-day6-cheat1-20261120-155620`) |
| **Cheat 2 (Interior small words)** | `< 0.20` | **`0.000000`** | `proof/cheats-reward.txt` (Job `lokesh-day6-cheat2-20261120-155730`) |
| **Cheat 3 (Combined partial port)** | `< 0.20` | **`0.000000`** | `proof/cheats-reward.txt` (Job `lokesh-day6-cheat3-20261120-155840`) |
| **New Control (Omit Mc rule)** | `< 0.20` | **`0.000000`** | `proof/cheats-reward.txt` (Job `lokesh-day6-mc-omission-20261120-162242`) |

Zero trial exceptions across all verification runs.

---

## 5. Five-Minute Defence Talk Script

- **0:00–0:45 — The Attack:**  
  *"On Day 4, my attacker Alok Kumar Jaiswal submitted three cheats against my task. His strongest cheat was a combined partial Go port that scored 0.905. It achieved this because my original verifier awarded 0.33 free points for compiling without Python files, and granted linear partial credit for an incomplete port without verifying edge cases like URLs and initialisms."*

- **0:45–1:45 — What Changed:**  
  *"To eliminate this exploit, I completely redesigned the verifier. First, I eliminated unearned structural points: `build` and `no_python` only pay out if the solution achieves at least 98% behavioural accuracy. Second, I replaced the fragile tab-delimited awk comparator with a streaming byte-exact Python comparator. Third, I addressed Alok's review by enforcing clean process exit status and exact 100,000 line count matching."*

- **1:45–2:45 — The 100K Exam:**  
  *"I scaled the exam from 2,000 to 100,000 inputs generated with seed 1. Answers were frozen twice in standard `re` mode (titlecase WITHOUT regex), producing 100,000 stable records with 0 dropped. The mode is explicitly stated in `instruction.md`."*

- **2:45–3:45 — Before and After Scores:**  
  *"On Day 6, Alok re-tested all three of his cheats, plus an extra cheat that omitted the `Mc` prefix rule. Every single cheat dropped from up to 0.905 down to 0.000. My oracle retained a perfect 1.000, and the Nop baseline scored 0.000. All cheats were completely closed."*

- **3:45–4:30 — Port Comparison:**  
  *"Evaluating two classmates' ports (Neha Gaur and Saurabh Baghel) on the new exam revealed that both missed exactly 3,520 cases out of 100,000. Both had scored 1.0 on the old 2,000 exam. The statistical probability of a 2,000 random sample catching these flaws was 0%, demonstrating that the 100K exam was essential to differentiate true complete ports from plausible partial implementations."*

- **4:30–5:00 — Surprises & Conclusion:**  
  *"The biggest surprise was discovering 3 bugs in my own Go oracle when tested against 100K inputs: version preservation (`v1.2`), leading underscores (`_dream`), and initialism dot loss (`v._`). Fixing those bugs brought my oracle to a verified 0 wrong answers out of 100,000. My task is now fast (75s execution), mathematically sound, and cheat-proof."*

---

## 6. Anticipated Questions & Defense

- **Q: Why require $\ge 98\%$ accuracy before awarding build and no_python points?**  
  *A:* The goal of the benchmark is to test functional headline capitalization in Go. A program that compiles and deletes Python files but fails headline casing has done zero useful work. Gating structural rewards behind functional competency ensures agents only get rewarded when they actually solve the problem.

- **Q: Why mode `re` and not `regex`?**  
  *A:* The upstream `python-titlecase` package uses the Python standard library `re` by default. The optional third-party `regex` module introduces divergent Unicode casing rules. Standard `re` is deterministic, dependency-free, and produced 0 unstable answers across the entire 100,000 candidate dataset.

- **Q: How did you address the static review critique regarding line counts and exit status?**  
  *A:* In `test.sh`, the comparator captures the candidate binary's exit status (`binary_exit=$?`) and requires code `0`. In Python, `itertools.zip_longest` counts both actual and expected lines; any line count discrepancy immediately sets the behaviour score to `0.0`.
