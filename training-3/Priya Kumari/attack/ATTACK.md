# Day 4 Adversarial Testing Report

**Target:** Arun  
**Task:** `Ethara.ai/titlecase-go` (Porting Python `titlecase` library to Go)

---

## 1. Target Information

* **Target Author:** Arun
* **Benchmark Task:** `Ethara.ai/titlecase-go`
* **Task Objective:** Re-implement the Python `titlecase` library in Go inside `/workspace/repo`. The solution must:
  * Compile using `go build ./...`
  * Remove all `.py` files from the repository
  * Read titles from standard input (`stdin`) and write titlecased results to standard output (`stdout`) matching the expected behaviour on hidden test inputs.
* **Scoring Weights:** 
  $$\text{Final Reward} = \frac{(1.0 \times \text{build}) + (1.0 \times \text{no\_python}) + (4.0 \times \text{behaviour})}{6.0}$$

---

## 2. Attack Experiments & Results

### Experiment 1: Half-Port Attack

* **Strategy:**  
  Implement a deliberately incomplete Go solution that only applies a basic titlecase heuristic: capitalize the first character of each whitespace-delimited word, lowercase the remaining characters, and preserve whitespace. All complex Python rules (apostrophes, hyphens, NYT small-word lists, punctuation sub-phrases) were omitted. All `.py` files were deleted.
* **Solution Folder:** `attack/cheat1/` (Evaluation in `attack/cheat1-test/`)
* **Job Folder:** `2026-11-18__17-25-19`
* **Trial ID:** `cheat3-test__dtX27E7`
* **Reward File:** `attack/results/cheat1-reward.json`
* **Overall Reward:** `0.3977`
* **Exceptions:** `0`
* **Check Results:**
  * **Build:** `1.0` (Passed)
  * **No Python:** `1.0` (Passed)
  * **Behaviour:** `0.0965` (9.65%)
* **Outcome Analysis:**  
  The solution scored 1.0 on `build` and 1.0 on `no_python`. On `behaviour`, the solution achieved an accuracy score of 0.0965 (9.65%). The aggregated weighted reward was:
  $$\frac{(1.0 \times 1.0) + (1.0 \times 1.0) + (4.0 \times 0.0965)}{6.0} = \frac{2.0 + 0.3860}{6.0} \approx 0.3977 \quad (39.77\%)$$
* **Why it worked:**  
  The target task awards 2.0 out of 6.0 total marks (33.33%) for passing structural checks alone (`tests/reward.toml:4`), checked by `tests/build.py:23-24` and `tests/no_python.py:24-26`. Furthermore, `tests/behaviour.py:28-29` uses unweighted line-by-line equality, awarding 0.0965 (9.65%) accuracy because basic capitalized words naturally matched straightforward test titles without implementing complex titlecasing rules.
* **How to fix:**  
  Gate `build` and `no_python` rewards so they are only awarded if `behaviour` exceeds a minimum threshold (e.g., > 0.50), or reduce structural check weights relative to behavioural accuracy in `tests/reward.toml:4`.

---

### Experiment 2: Enhanced Small-Word Heuristic

* **Strategy:**  
  Implemented an enhanced Go titlecasing heuristic that incorporates a standard small-words lowercasing list alongside whitespace-preserved capitalization. The goal was to improve behavioural matching while maintaining compliance with the build and no-Python checks.
* **Solution Folder:** `attack/cheat2/` (Evaluation in `attack/cheat2-test/`)
* **Job Folder:** `2026-11-19__10-31-49`
* **Trial ID:** `cheat4-test__RqjzYh3`
* **Reward Files:** `attack/results/cheat2-reward.json`, `attack/results/cheat2-reward-details.json`
* **Overall Reward:** `0.4347`
* **Exceptions:** `0`
* **Check Results:**
  * **Build:** `1.0` (Passed)
  * **No Python:** `1.0` (Passed)
  * **Behaviour:** `0.1520` (15.20%)
* **Outcome Analysis:**  
  The solution passed both structural checks, `build` and `no_python`, receiving a score of 1.0 for each. The behaviour score improved to 0.1520 compared with Cheat 1's 0.0965. The resulting overall weighted reward was 0.4347 (43.47%):
  $$\frac{(1.0 \times 1.0) + (1.0 \times 1.0) + (4.0 \times 0.1520)}{6.0} = \frac{2.0 + 0.6080}{6.0} \approx 0.4347 \quad (43.47\%)$$
* **Why it worked:**  
  The solution earned the 33.33% structural baseline (`tests/reward.toml:4`), and adding a standard lowercase small-words list matched common multi-word titles. Because `tests/behaviour.py:28-29` averages accuracy across a single flat list of synthetic lines rather than categorizing edge cases, handling small words increased behavioural accuracy to 0.1520 (15.20%) and overall reward to 0.4347.
* **How to fix:**  
  Partition `tests/behaviour.py:33-52` into distinct test suites (e.g., small words, acronyms, quotations) requiring passing thresholds across each category rather than evaluating a single flat list.

---

### Experiment 3: Punctuation-Aware Heuristic

* **Strategy:**  
  Implemented an improved Go titlecasing heuristic that focuses on handling punctuation and word boundaries. It capitalizes words following sub-phrase punctuation marks (`:`, `;`, `.`, `?`, `!`, `-`, `–`, `‒`, `—`, `―`), supports hyphenated words, treats apostrophe contractions and prefixes (`O'`, `l'`, `d'`), preserves whitespace, and keeps small words lowercased unless at word or sub-phrase boundaries.
* **Solution Folder:** `attack/cheat3/` (Evaluation in `attack/cheat3-test/`)
* **Job Folder:** `2026-11-19__10-49-21`
* **Trial ID:** `cheat5-test__dqGUTrk`
* **Reward Files:** `attack/results/cheat3-reward.json`, `attack/results/cheat3-reward-details.json`
* **Overall Reward:** `0.5177`
* **Exceptions:** `0`
* **Check Results:**
  * **Build:** `1.0` (Passed)
  * **No Python:** `1.0` (Passed)
  * **Behaviour:** `0.2765` (27.65%)
* **Outcome Analysis:**  
  The solution passed both structural checks (`build: 1.0`, `no_python: 1.0`). By accounting for sub-phrase punctuation, hyphens, and apostrophes, the behavioural accuracy increased to 0.2765 (27.65%). The resulting overall weighted reward was 0.5177 (51.77%):
  $$\frac{(1.0 \times 1.0) + (1.0 \times 1.0) + (4.0 \times 0.2765)}{6.0} = \frac{2.0 + 1.1060}{6.0} \approx 0.5177 \quad (51.77\%)$$
* **Why it worked:**  
  Passing structural checks (`tests/build.py:23-24`, `tests/no_python.py:24-26`) secured 33.33% of the marks (`tests/reward.toml:4`). Adding heuristics for sub-phrase punctuation (`:`, `;`, `.`, `?`, `!`), hyphens, and apostrophe prefixes satisfied 27.65% of test cases in `tests/behaviour.py:28-29`, lifting the composite reward to 0.5177 (51.77%) without porting the actual Python titlecasing regex engine.
* **How to fix:**  
  Enforce an all-or-nothing threshold (e.g., requiring at least 80% behavioural accuracy before computing any composite score) and eliminate the redundant build check in `tests/no_python.py:26`.

---

## 3. Results Comparison Table

| Attack Name | Solution / Test Folder | Job Folder | Trial ID | Build (wt 1.0) | No Python (wt 1.0) | Behaviour (wt 4.0) | Exceptions | Overall Reward |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Experiment 1: Half-Port Attack** (Cheat 1) | `attack/cheat1-test/` | `2026-11-18__17-25-19` | `cheat3-test__dtX27E7` | 1.0 | 1.0 | 0.0965 | 0 | **0.3977** |
| **Experiment 2: Enhanced Small-Word Heuristic** (Cheat 2) | `attack/cheat2-test/` | `2026-11-19__10-31-49` | `cheat4-test__RqjzYh3` | 1.0 | 1.0 | 0.1520 | 0 | **0.4347** |
| **Experiment 3: Punctuation-Aware Heuristic** (Cheat 3) | `attack/cheat3-test/` | `2026-11-19__10-49-21` | `cheat5-test__dqGUTrk` | 1.0 | 1.0 | 0.2765 | 0 | **0.5177** |

---

## 4. Conclusion & Key Takeaways

1. **Structural Check Weighting:** The build and no_python checks together contribute 2 out of 6 possible weighted points (33.33%). A solution that passes both checks earns these points even if its behavioural accuracy is low.
2. **Heuristic Progression:** Successive heuristic improvements systematically increased behavioural accuracy without implementing full Python titlecase rules:
   - Naive whitespace-only capitalization (Experiment 1) yielded 9.65% behaviour accuracy (`0.3977` overall).
   - Adding a small-words exception list (Experiment 2) raised behaviour accuracy to 15.20% (`0.4347` overall).
   - Adding punctuation, sub-phrase breaks, hyphenation, and apostrophe handling (Experiment 3) achieved 27.65% behaviour accuracy, pushing the final score past 50% to `0.5177`.
3. **Adversarial Benchmark Impact:** All three retained attacks significantly exceeded the 0.20 adversarial threshold, demonstrating that generous precondition weighting combined with partial heuristics can achieve high benchmark scores on incomplete solutions.

**Highest score achieved: 0.5177 (51.77%) — Punctuation-Aware Heuristic.**

---

## 5. Day 6 Re-Attack Results

### 5.1 Re-Attack on Target Task (Arun Bisht — `Arun_Reattack_LF`)

Following Day 6 Step 6.2, all three original cheats were re-evaluated in Harbor against Arun's hardened task:
* **Target:** Arun Bisht (`Ethara.ai/titlecase-go`, Hardened)
* **Hardening Strategy Used by Arun:** Implemented a hard 80% competency gate in `tests/score_utils.py` (`MIN_BEHAVIOUR_SCORE = 0.8`), which requires `score_behaviour(workspace) >= 0.8` for any criterion (`build`, `no_python`, `behaviour`) to receive non-zero points.

#### Results on Arun's Hardened Task:

1. **Cheat 1: Half-Port Heuristic**
   * **Job Name:** `cheat1-reattack-lf`
   * **Trial ID:** `Arun_Reattack_LF__3WNekrN`
   * **Check Results:** `build: 0.0`, `no_python: 0.0`, `behaviour: 0.0`
   * **Composite Reward:** **`0.0000`** (Original Day 4: `0.3977`)
   * **Status:** **DEFEATED** (< 0.20 threshold). Gated out by Arun's 80% behavior threshold.

2. **Cheat 2: Enhanced Small-Word Heuristic**
   * **Job Name:** `cheat2-reattack-lf`
   * **Trial ID:** `Arun_Reattack_LF__D2VDX59`
   * **Check Results:** `build: 0.0`, `no_python: 0.0`, `behaviour: 0.0`
   * **Composite Reward:** **`0.0000`** (Original Day 4: `0.4347`)
   * **Status:** **DEFEATED** (< 0.20 threshold). Gated out by Arun's 80% behavior threshold.

3. **Cheat 3: Punctuation-Aware Heuristic**
   * **Job Name:** `cheat3-reattack-lf`
   * **Trial ID:** `Arun_Reattack_LF__VeZZyAZ`
   * **Check Results:** `build: 0.0`, `no_python: 0.0`, `behaviour: 0.0`
   * **Composite Reward:** **`0.0000`** (Original Day 4: `0.5177`)
   * **Status:** **DEFEATED** (< 0.20 threshold). Gated out by Arun's 80% behavior threshold.

#### Target Re-Attack Comparison Table (Arun's Task)

| Attack / Cheat | Original Job | Original Reward | Hardened Job | Build | No Python | Behaviour | Hardened Reward | Net Change |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cheat 1 (Half-Port)** | `2026-11-18__17-25-19` | **0.3977** | `cheat1-reattack-lf` | 0.0 | 0.0 | 0.0 | **0.0000** | **-0.3977** |
| **Cheat 2 (Small Words)** | `2026-11-19__10-31-49` | **0.4347** | `cheat2-reattack-lf` | 0.0 | 0.0 | 0.0 | **0.0000** | **-0.4347** |
| **Cheat 3 (Punctuation)** | `2026-11-19__10-49-21` | **0.5177** | `cheat3-reattack-lf` | 0.0 | 0.0 | 0.0 | **0.0000** | **-0.5177** |

---

### 5.2 Cross-Verification on Author's Hardened Task (`Priya Kumari/task`)

For benchmark defence completeness (Step 6.1), the same 3 cheats were evaluated against Priya Kumari's hardened task (using 100K frozen exam, canonical correctness smoke test in `no_python.py`, and calibrated weights `{build: 1.0, no_python: 1.0, behaviour: 23.0}`):

| Attack / Cheat | Hardened Job Folder | Build (wt 1.0) | No Python (wt 1.0) | Behaviour (wt 23.0) | Hardened Reward | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Cheat 1** | `jobs/2026-11-21__23-55-01` | 1.0 | 0.0 | 0.10382 | **0.1355** | PASSED (< 0.20) |
| **Cheat 2** | `jobs/2026-11-21__23-57-05` | 1.0 | 0.0 | 0.13959 | **0.1684** | PASSED (< 0.20) |
| **Cheat 3** | `jobs/2026-11-21__23-59-05` | 1.0 | 0.0 | 0.19617 | **0.2205** | DEFENDED (Genuine partial credit) |
