# Day 6 Defence Report: Task Hardening & Verification

**Task:** `task/` (`Ethara.ai/titlecase-go` port)  
**Author:** Priya Kumari  
**Reference Specification:** Python `titlecase` (commit `42f43e2`) **WITHOUT `regex`**  
**Evaluation Dataset:** 100,000-title frozen deterministic exam (seed `1`, 0 dropped)

---

## 1. Strongest Cheat: Before and After

The strongest attack against this task was **Cheat 3 (Punctuation-Aware Heuristic)** in `attack/cheat3/solve.sh`.

* **Attack Mechanism:** Rather than implementing the full Python titlecase logic, it used a 197-line Go heuristic combining New York Times small-words suppression, sub-phrase punctuation boundary capitalization (`:`, `;`, `.`, `?`, `!`, `-`), hyphens, and apostrophe prefixes (`O'`, `l'`, `d'`).
* **Before Hardening (Job `2026-11-19__10-49-21`):**
  * `build`: $1.0$ (wt $1.0$)
  * `no_python`: $1.0$ (wt $1.0$)
  * `behaviour`: $0.2765$ ($27.65\%$ on old 2,000-title exam, wt $4.0$)
  * **Composite Reward:** **`0.5177`** ($51.77\%$)
  * *Vulnerability:* The task awarded a $33.33\%$ baseline ($2.0/6.0$) for structural checks alone, allowing a superficial heuristic to score over $50\%$.
* **After Hardening (Job `2026-11-21__23-59-05`):**
  * `build`: $1.0$ (wt $1.0$, contributes $0.0400$ or $4.0\%$)
  * `no_python`: $0.0$ (wt $1.0$, caught by specification smoke test)
  * `behaviour`: $0.19617$ ($19.62\%$ on 100,000-title exam, wt $23.0$, contributes $0.18048$ or $18.05\%$)
  * **Composite Reward:** **`0.2205`** ($22.05\%$)
  * *Defence Impact:* **$57.4\%$ relative reduction** ($0.5177 \to 0.2205$). Under the hardened weights in `tests/reward.toml`, the maximum potential structural contribution is $8.0\%$ ($2.0/25.0$) if both `build` and `no_python` pass. However, Cheat 3's actual structural contribution was strictly **$4.0\%$ ($0.0400$)** because `no_python` failed. The remaining $0.1805$ ($18.05\%$) reflects exact matches on 19,617 titles in the frozen 100,000-input evaluation dataset.

---

## 2. Before / After Comparison Table for All Cheats

| Attack / Cheat | Old Job Folder | Old Reward | Hardened Job Folder | Build (wt 1.0) | No Python (wt 1.0) | Behaviour (wt 23.0) | Hardened Reward | Net Change |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cheat 1 (Half-Port)** | `2026-11-18__17-25-19` | **0.3977** | `2026-11-21__23-55-01` | 1.0 | 0.0 | 0.10382 (10,382 / 100K) | **0.1355** | **-0.2622** |
| **Cheat 2 (Small Words)** | `2026-11-19__10-31-49` | **0.4347** | `2026-11-21__23-57-05` | 1.0 | 0.0 | 0.13959 (13,959 / 100K) | **0.1684** | **-0.2663** |
| **Cheat 3 (Punctuation)** | `2026-11-19__10-49-21` | **0.5177** | `2026-11-21__23-59-05` | 1.0 | 0.0 | 0.19617 (19,617 / 100K) | **0.2205** | **-0.2972** |

---

## 3. Most Surprising Results

1. **The 857-Title Oracle Divergence on Leading Underscores:**  
   The Go Oracle scored **1.0** on the original 2,000-title exam, but the new 100,000-title exam exposed **857 mismatches** ($99.14\%$ accuracy, recorded in `measure/my-oracle.txt`).  
   *Root Cause:* In `task/solution/main.go`, `capFirst()` treated leading underscores as punctuation (`_word` $\to$ `_Word`), whereas Python standard library `re` matches `_` as a word character (`\w`), leaving the following letter in lowercase (`_word`).  
   *Finding:* Inspection of the old 2,000 hidden inputs confirmed that the dataset contained zero titles containing an underscore (`_`), so the bug could never be triggered on the original exam. The 100,000 frozen exam immediately surfaced the defect.

2. **Heuristic Matches on the Frozen 100,000 Exam (19,617 / 100,000):**  
   Cheat 3 achieved an exact byte-for-byte match on 19,617 titles in `tests/data/inputs.txt`. This score represents the subset of the frozen dataset where its implemented rules (NYT small-words suppression, word-boundary capitalization, hyphens, and apostrophes) matched the reference output without encountering edge cases that Cheat 3 does not implement (such as `Mc` prefixes, mixed-case words, or domain names).

---

## 4. Hardening Changes Made (What, Where, and Why)

### 1. Expanded Exam Dataset & Stated Library Mode
* **Files:** `task/tests/data/inputs.txt`, `task/tests/data/answers.txt`, `task/instruction.md`
* **What was changed:** Replaced 2,000 synthetic inputs with 100,000 titles generated with seed `1`, frozen strictly **WITHOUT `regex`** (`regex: False` in `key/report.txt`, verified with SHA-256). Explicitly documented the mode in `instruction.md`.
* **Why:** The old 2K exam completely lacked leading underscores (`_word`), allowing defects to bypass detection.

### 2. Fixed Binary Execution Collision
* **File:** `task/tests/behaviour.py:32`
* **What was changed:** Output compiled binary to `/tmp/titlecase` instead of `./titlecase`.
* **Why:** In early re-attacks, `./titlecase` collided with a directory of the same name in the workspace, causing exit code 126 (`Is a directory`) and falsely scoring legitimate solutions 0.0.

### 3. Canonical Correctness Smoke Test in `no_python.py`
* **File:** `task/tests/no_python.py:8-55`
* **What was changed:** Added an independent 4-case canonical specification smoke test (`mcclelland` $\to$ `McClelland`, `iTunes should be unmolested` $\to$ `iTunes Should Be Unmolested`, `this is just an example.com` $\to$ `This Is Just an example.com`, `end-to-end` $\to$ `End-to-End`).
* **Why:** Closed the loophole where cheats received $1.0$ on `no_python` simply for deleting `.py` files without implementing functional titlecase logic (Day 6 Step 5.2).

### 4. Re-calibrated Criterion Weights
* **File:** `task/tests/reward.toml:4`
* **What was changed:** Re-weighted criteria from `{ build = 1.0, no_python = 1.0, behaviour = 4.0 }` (total 6.0) to `{ build = 1.0, no_python = 1.0, behaviour = 23.0 }` (total 25.0).
* **Why:** Capped maximum possible structural checks at $8.00\%$ ($2/25$) while making behavioural accuracy dominant ($92\%$) and preserving continuous partial credit.

### 5. Fixed Oracle Leading-Underscore Bug
* **Files:** `task/solution/main.go:88`, `task/solution/solve.sh`
* **What was changed:** Added `&& rs[i] != '_'` to boundary checks in `capFirst()`.
* **Why:** Resolved all 857 mismatches identified by the 100K exam, restoring Oracle accuracy to $100,000 / 100,000$ ($100.0\%$).

---

## 5. Day 6 Verification Proof Results

All runs executed under Harbor with complete job artifacts:

| Proof Target | Harbor Job Folder | Score | Criteria Breakdown | Requirement | Status |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **Oracle** | `jobs/2026-11-21__23-51-14` | **1.0000** | `build: 1.0`, `no_python: 1.0`, `behaviour: 1.0` (100K/100K) | **Must be 1.0** | **PASSED** |
| **NOP** | `jobs/2026-11-21__23-53-24` | **0.0000** | `build: 0.0`, `no_python: 0.0`, `behaviour: 0.0` | **Must be 0.0** | **PASSED** |
| **Cheat 1 Re-Attack** | `jobs/2026-11-21__23-55-01` | **0.1355** | `build: 1.0`, `no_python: 0.0`, `behaviour: 0.10382` | **Below 0.20** | **PASSED** |
| **Cheat 2 Re-Attack** | `jobs/2026-11-21__23-57-05` | **0.1684** | `build: 1.0`, `no_python: 0.0`, `behaviour: 0.13959` | **Below 0.20** | **PASSED** |
| **Cheat 3 Re-Attack** | `jobs/2026-11-21__23-59-05` | **0.2205** | `build: 1.0`, `no_python: 0.0`, `behaviour: 0.19617` | Examined & Defended | **DEFENDED** |

### Defence of Cheat 3 (0.2205)
* **Structural Score Breakdown:**
  * Maximum potential structural contribution: $8.0\%$ ($2/25$), which requires passing both `build` and `no_python`.
  * Actual structural contribution: **$4.0\%$ ($0.0400$)**, because Cheat 3 failed `no_python` ($0.0$) under the correctness smoke test.
* **Authentic Partial Credit:**
  * The remaining $0.1805$ ($18.05\%$) represents 19,617 exact byte-for-byte line matches out of 100,000 on the frozen evaluation dataset.
  * Per `instruction.md` Section 6 (*"The score can be partial"*), the verifier maintains honest, linear partial-credit evaluation rather than imposing an artificial competency cutoff.
