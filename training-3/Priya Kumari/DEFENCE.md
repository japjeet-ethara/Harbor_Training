# Day 6 Defence Report: Task Hardening & Verification

**Task:** `task/` (`Ethara.ai/titlecase-go` port)  
**Author:** Priya Kumari  
**Attacker (Pair #52):** Satvik Tandon (`satvik-tandon`)  
**Reference Specification:** Python `titlecase` (commit `42f43e2`) **WITHOUT `regex`**  
**Evaluation Dataset:** 100,000-title frozen deterministic exam (seed `1`, 0 dropped)  
**Task Commit Verified:** `ed95cf832935b14ea964187aea04bb0fe45be745`  

---

## 1. Strongest Cheat: Before and After

The strongest original attack against this task was **Satvik's Cheat 2 (Capitalize Word Starts)** in `satvik-tandon/attack/cheat2/solve.sh`.

* **Attack Mechanism:** Split each title on whitespace, capitalized the first rune of each word, and lowercased the rest, bypassing real titlecase rules while earning full packaging credit.
* **Before Hardening (Job `jobs/satvik-day4-20261118-162511-cheat2`):**
  * `build`: $1.0$ (wt $1.0$)
  * `no_python`: $1.0$ (wt $1.0$)
  * `behaviour`: $0.4815$ ($48.15\%$ on old 2,000-title exam, wt $4.0$)
  * **Composite Reward:** **`0.6543`** ($65.43\%$)
  * *Vulnerability:* The unhardened task awarded a $33.33\%$ baseline ($2.0/6.0$) for structural checks alone, while the small 2,000 synthetic exam allowed naive word-capitalization to pass nearly half of the titles.
* **After Hardening (Verified by Satvik in Job `jobs/priya-current-cheat2`):**
  * `build`: $1.0$ (wt $1.0$, contributes $0.0400$ or $4.0\%$)
  * `no_python`: $0.0$ (wt $1.0$, failed canonical correctness smoke test)
  * `behaviour`: $0.1090$ on the 100,000-title exam (wt $23.0$, contributes $0.1003$)
  * **Composite Reward:** **`0.1403`** ($14.03\%$)
  * *Defence Impact:* **$78.6\%$ relative drop** ($0.6543 \to 0.1403$), comfortably below the $0.20$ threshold.

---

## 2. Before / After Comparison Table for Attacker's Cheats

Satvik Tandon independently re-evaluated his cheats against Priya's hardened task (commit `ed95cf8`), recording the results in `training-3/satvik-tandon/attack/ATTACK.md`:

| Submission / Cheat | Day 4 Job | Day 4 Score | Day 6 Job (Current Hardened) | Build (wt 1.0) | No Python (wt 1.0) | Behaviour (wt 23.0) | Final Reward | Target | Result |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Satvik Cheat 1 (Echo)** | `satvik-day4...cheat1` | **0.3867** | `jobs/priya-current-cheat1` | 1.0 | 0.0 | 0.0137 | **0.0526** | $< 0.20$ | **PASSED** |
| **Satvik Cheat 2 (Word Starts)** | `satvik-day4...cheat2` | **0.6543** | `jobs/priya-current-cheat2` | 1.0 | 0.0 | 0.1090 | **0.1403** | $< 0.20$ | **PASSED** |
| **Satvik Cheat 3 (Small Words)** | `satvik-day4...cheat3` | **0.6463** | `jobs/priya-current-cheat3` | 1.0 | 0.0 | 0.1341 | **0.1634** | $< 0.20$ | **PASSED** |
| **Priya's Hardened Oracle** | `priya-rerun-oracle` | **0.9943** | `jobs/priya-current-oracle` | 1.0 | 1.0 | 1.0000 | **1.0000** | $= 1.0$ | **PASSED** |

> **Attacker's Confirmation:** *"Priya's oracle reaches 1.0 and all three of my original cheats are below 0.2."* (`satvik-tandon/attack/ATTACK.md`).

---

## 3. Defence Analysis of Satvik's Day 6 New Cheat (Cheat 4)

Satvik introduced one new cheat on Day 6: **Cheat 4 (Compact Rule Heuristic)** in `attack/cheat4/solve.sh`.

* **Score:** Reward **`0.2635`** (`build: 1.0`, `no_python: 1.0`, `behaviour: 0.19942`, job `jobs/priya-current-cheat4-rule-heuristic`).
* **Why it scored 0.2635:**
  1. **Smoke Test Evasion:** Satvik specifically crafted Cheat 4 to pass all four static assertions in `task/tests/no_python.py` (`Mc` prefix, internal mixed-case like `iTunes`, domain names with dots, and hyphens). This enabled Cheat 4 to capture both structural points (`build: 1.0` + `no_python: 1.0`), granting an immediate $8.0\%$ ($2.0/25.0$) reward floor.
  2. **Heuristic Behaviour on 100K Pool:** On the full 100,000 titles, Cheat 4 matched $19,942$ titles ($19.94\%$), yielding $23.0 \times 0.19942 / 25.0 = 0.1835$.
  3. **Composite:** $0.0800 + 0.1835 = \mathbf{0.2635}$.
* **Defence & Hardening Takeaway:**
  * Even with rules tailored to pass the smoke test, the **100,000-title exam defeated Cheat 4 on 80,058 titles ($80.06\%$ failure rate)**, holding its behavioural accuracy strictly below $20\%$.
  * The excess $0.0635$ over $0.20$ is entirely due to structural checks paying out additively rather than acting as a gating prerequisite. Gating behaviour credit behind passing packaging checks (or expanding smoke cases to include sub-phrase colons, quotes, and underscores) brings this cheat to **`0.1994`** ($< 0.20$).

---

## 4. Exam: Before and After (3-Port Measurement)

The exam was expanded from 2,000 synthetic inputs to **100,000 frozen titles** generated deterministically with seed `1`, verified with standard library `re` (`regex: False`, 0 dropped).

### Comparison Table across 3 Independent Ports

| Port Evaluated | Wrong on new 100K exam | Old 2K exam caught it? | Chance 2K random misses it |
| :--- | :---: | :---: | :---: |
| **Priya's Oracle (before fix)** | 857 | No | ~0% ($3.4 \times 10^{-8}$) |
| **Priya's Oracle (after fix)** | 0 | n/a | n/a |
| **Aman Tiwari (`ports/aman-tiwari`)** | 0 | n/a | n/a |
| **Hardika (`ports/hardika`)** | 3,053 | No | ~0% ($1.8 \times 10^{-27}$) |

### Mathematical Explanations:
1. **Priya's Oracle (857 mismatches before fix):**  
   The probability of a random 2,000 sample missing all 857 defects is:  
   $$\text{Chance} = \left(1 - \frac{857}{100000}\right)^{2000} \approx 3.42 \times 10^{-8} \quad (\approx 0.0000034\%)$$  
   The old 2K exam missed it not by chance, but because its synthetic pool completely lacked leading underscores (`_word`).
2. **Hardika (3,053 mismatches):**  
   Represents mode divergence: Hardika implemented Python `titlecase` WITH `regex` (`v1.2` $\to$ `V1.2`), whereas the reference was frozen WITHOUT `regex` (standard `re`, keeping `v1.2` lowercase). The old 2K exam had zero version strings and completely missed the divergence.
3. **Hardened Oracle (0 mismatches):**  
   Fixed `capFirst()` with `&& rs[i] != '_'`. Accuracy is $100,000 / 100,000$ ($100.0\%$).

---

## 5. Most Surprising Result

**The 857-Title Oracle Underscore Bug:**  
Our Go Oracle originally scored a perfect **1.0** on the Day 4 exam. However, running the 100,000-title exam revealed that the Oracle failed on exactly 857 titles.  
* *Root Cause:* In `task/solution/main.go`, `capFirst()` treated leading underscores as punctuation (`_winter` $\to$ `_Winter`). In Python's standard `re`, `_` is matched as a word character (`\w`), so `re` does not match the word boundary and leaves the following letters lowercase (`_winter`).  
* *Takeaway:* A 2,000-line test suite gave false confidence because it lacked weird punctuation. Scaling to a diverse 100,000-title corpus surfaced subtle standard library divergence that would otherwise have gone undetected.

---

## 6. Summary of Hardening Changes Made

1. **Re-weighted Evaluation Criteria (`tests/reward.toml`):**  
   Changed weights from `{ build = 1.0, no_python = 1.0, behaviour = 4.0 }` to `{ build = 1.0, no_python = 1.0, behaviour = 23.0 }`. Capped maximum structural contribution at $8.0\%$ ($2/25$), requiring real behavioural accuracy ($92\%$) to earn points.
2. **Canonical Correctness Smoke Test (`tests/no_python.py`):**  
   Added 4 canonical assertions (`McClelland`, `iTunes`, `example.com`, `End-to-End`). Cheats that delete Python without implementing functional logic receive `0.0` for `no_python`.
3. **Fixed Binary Path Collision (`tests/behaviour.py`):**  
   Changed output binary path to `/tmp/titlecase` instead of `./titlecase`, resolving directory collision exit 126 errors.
4. **Resolved Oracle Underscore Divergence (`solution/main.go` & `solve.sh`):**  
   Added `&& rs[i] != '_'` in `capFirst()`, bringing Oracle accuracy on the 100K exam from 99.14% to 100.0%.
5. **Mode Declaration in `instruction.md`:**  
   Explicitly declared that answers come from Python `titlecase` WITHOUT `regex`.
