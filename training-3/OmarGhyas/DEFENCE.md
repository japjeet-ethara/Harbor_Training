# DEFENCE.md — Day 6 Defense Presentation Notes

**Task:** `training-3/OmarGhyas/task` (`titlecase-go`)  
**Author:** Omar Ghyas  
**Attacker:** Ashish (`training-3/Ashish-Reference/attack/ATTACK.md`)  
**Target Hardened Commit:** `9e43b9c8d360416a27836166947c18f6f4008da8`  
**Evaluation Framework:** Harbor 0.25.0 (`golang:1.23`, `harbor-rewardkit==0.2.*`)  
**Target Answer Engine:** Python `titlecase 2.4.1` with `regex` module enabled  

---

## 1. Strongest Cheat

### Identification: Cheat 2 — Half Port (`cheat2/solve.sh`)
- **Original Score (Day 4):** `0.7213` (Build: `1.0`, No-Python: `1.0`, Behaviour: `0.5820`, Overall: `(1 + 1 + 4×0.5820)/6 = 0.7213`)
- **Ashish Day 6 Re-attack Score (Pre-threshold):** `0.2936` (Build: `1.0` [wt 0], No-Python: `1.0` [wt 0], Behaviour: `0.2936` [wt 1.0])
- **Final Hardened Score (Day 6 with Threshold):** **`0.0000`** (Job: `day6-phase3-cheat2`, Trial: `task__6Wz8s3h`)

### Why It Was Effective:
1. **Unearned Baseline from Standard Words:** The half-port implements only trivial titlecase rules (capitalizing each whitespace-separated token, lowercasing a small-word list, and capitalizing the first/last word). It completely ignores hyphens, slashes, apostrophes, acronyms, Mac/Mc names, subphrases, and Unicode.
2. **Linear Scoring Trap:** In the pre-threshold verifier (`matches / len(expected)`), every standard sentence matched by chance awarded free linear credit. Even across a dense 100,000-line exam, standard English casing matches 29,363 lines (29.36%), automatically securing `0.2936 > 0.20` with zero complex logic.

### How It Was Addressed:
1. **Full Behavioral Weighting (Day 5):** Reconfigured `reward.toml` to assign 100% weight to `behaviour` (`weights = { build = 0.0, no_python = 0.0, behaviour = 1.0 }`), stripping the 0.3333 free structural points.
2. **90% Quality Floor (Day 6):** Replaced linear scoring with a strict threshold gate in `task/tests/support.py`:
   $$\text{rate} = \frac{\text{matches}}{\text{len}(\text{expected})}$$
   $$\text{return } 0.0 \text{ if } \text{rate} < 0.90 \text{ else } \frac{\text{rate} - 0.90}{0.10}$$
   A port achieving 29.36% match rate receives **`0.0000`**, while genuine ports achieving $\ge 90\%$ accuracy receive smooth, proportional partial credit in $[0.0, 1.0]$.

---

## 2. Before / After Exam Results

### Exam Scale Comparison
- **Old Exam (Day 4):** 2,000 inputs (`tests/data/hidden.jsonl`, seed 1).
- **New Exam (Days 5–6):** Exactly **100,000** inputs (`tests/data/inputs.txt`), frozen with Python `titlecase 2.4.1` in `regex` mode (`tests/data/answers.txt`, 0 dropped).

### Verified Port Measurements (from `HARDEN.md` and `measure/`)
The table below compares verified test measurements of different Go ports evaluated against the 100,000-line exam suite:

| Port Implementation | Wrong on 100K Exam | Error Rate | Old 2K Exam Caught It? | Chance 2K Misses It | Measured Reward |
|---|:---:|:---:|:---:|:---:|:---:|
| **`my-oracle` (`solution/solve.sh`)** | **0 of 100,000** | **0.00%** | No (0 errors; 100% pass) | 100% | **1.0000** |
| **`AlokKumarJaiswal`** | 30,142 of 100,000 | 30.14% | Yes (301 of 2,000 errors) | 0% | 0.0000 (below 90%) |
| **`AmanTiwari`** | 3,053 of 100,000 | 3.05% | Yes (29 of 2,000 errors) | 0% | 0.6947 (re vs regex mode) |

### Key Observations:
- **`my-oracle`**: Passes 100,000 out of 100,000 cases byte-for-byte in Harbor, confirming zero false positives in the enlarged test suite.
- **`AlokKumarJaiswal`**: Fails 30.14% of inputs due to unhandled punctuation boundaries, subphrase casing, and multi-word hyphenation.
- **`AmanTiwari`**: Fails exactly 3,053 inputs (3.05%). This cleanly isolates engine semantics: Aman ported the standard-library `re` fallback, whereas `task/instruction.md` explicitly mandates the `regex` module.

---

## 3. Hardening Changes

### Day 5 Hardening Changes
1. **Answer Leak Removal:** Removed line 4 (`COPY visible.jsonl /workspace/repo/visible.jsonl`) from `environment/Dockerfile`, eliminating answer leakage to the agent workspace.
2. **Structural Decoupling Eliminated:** `task/tests/reward.toml` set `build = 0.0` and `no_python = 0.0`, weighting `behaviour = 1.0`.
3. **Strict Evaluation Prerequisites:** In `task/tests/support.py`, compilation (`go build ./...`) and absence of `.py` files were made non-negotiable gates:
   ```python
   if not go_build_succeeds(workspace) or not python_files_absent(workspace):
       return 0.0
   ```
4. **100K Frozen Dataset:** Scaled hidden inputs from 2,000 to 100,000 lines generated with `titlecase 2.4.1` in `regex` mode.

### Day 6 Hardening Changes
1. **Build-Context & Dependency Fix:**
   - Ashish reported that `harbor run -p task -a oracle` failed before grading because `task/environment/docker-compose.yaml` had obsolete paths (`context: ../..`, `dockerfile: titlecase-go/environment/Dockerfile`) and `python-titlecase` was not in the repo root.
   - **Fix:** Permanently removed `docker-compose.yaml` so Harbor builds `task/environment/Dockerfile` directly with context `task/environment/`.
   - Vendored clean `python-titlecase` 2.4.1 directly inside `task/environment/python-titlecase/` and tracked it in Git, making the task fully self-contained.
2. **Threshold-Based Behavioral Scoring:**
   - In `task/tests/support.py`, replaced raw linear accuracy with a 90% threshold formula:
     ```python
     rate = matches / len(expected)
     if rate < 0.90:
         return 0.0
     return (rate - 0.90) / 0.10
     ```
   - This neutralized naive ports while preserving full partial credit for genuine ports achieving $\ge 90\%$ accuracy.

---

## 4. Harbor Proof Results

All results below were executed and verified using Harbor on the hardened task (`training-3/OmarGhyas/task/`):

| Evaluation Run | Agent / Solver | Harbor Job Name | Harbor Job ID | Trial ID | Final Reward | Defense Condition Met? |
|---|---|---|---|---|:---:|:---:|
| **Oracle** | `solve.sh` | `day6-phase2-oracle` | `52d7045a-5801-46c5-a6ac-4c63594e61d6` | `task__4M28aT2` | **`1.0000`** | **PASS** (Reward = 1.0) |
| **NOP Baseline** | `nop` | `day6-phase3-nop` | `39d166d3-559a-42be-b475-572fd2c4a331` | `task__2tajihQ` | **`0.0000`** | **PASS** (Reward = 0.0) |
| **Cheat 1 (Lookup Table)** | `cheat1/solve.sh` | `day6-phase3-cheat1` | `d5c07eec-5c04-4fb4-ad3a-1d7a94019075` | `task__uVfrNjD` | **`0.0000`** | **PASS** (Reward < 0.20) |
| **Cheat 2 (Half Port)** | `cheat2/solve.sh` | `day6-phase3-cheat2` | `2ccd1bdd-465b-48f6-8e78-efe5867a4828` | `task__6Wz8s3h` | **`0.0000`** | **PASS** (Reward < 0.20) |
| **Cheat 3 (Silent Binary)** | `cheat3/solve.sh` | `day6-phase3-cheat3` | `7c13e795-fd8e-4f6b-927e-aa0dfa1032bc` | `task__42DoPXV` | **`0.0000`** | **PASS** (Reward < 0.20) |

### Deliverable Proof References
- Oracle verification: [`proof/oracle-reward.json`](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/proof/oracle-reward.json) (`1.0`)
- NOP baseline: [`proof/nop-reward.json`](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/proof/nop-reward.json) (`0.0`)
- Attacker cheats log: [`proof/cheats-reward.txt`](file:///c:/Users/Omarghyas/Desktop/Harbor_Training/training-3/OmarGhyas/proof/cheats-reward.txt) (All `0.0`)

---

## 5. Surprise and Limitations

### Genuine Surprising Finding
- **The Persistence of Linear Match Inflation:** The most counter-intuitive finding was that dramatically expanding the exam from 2,000 to 100,000 lines was **insufficient by itself** to defeat naive partial implementations. Because natural language text shares significant standard titlecasing conventions (e.g. capitalizing first letters), a simple half-port still scored nearly 30% without touching any difficult logic. Robust task evaluation strictly requires **non-linear scoring thresholds** that separate baseline linguistic overlap from genuine rule implementation.

### Unverified Limitation & Pending Hypothesis
- **Python Interpreter Exposure Hypothesis:**
  - Ashish reported a theoretical, unexploited vulnerability: the verifier Dockerfile (`golang:1.23`) inherits Debian's world-executable `/usr/bin/python3`. While the graded program runs as user `nobody` inside `/var/grader`, `nobody` still has execute permissions for system binaries.
  - Ashish hypothesized that an adversary could disguise the original Python code under a non-`.py` extension (e.g., `tc.txt`), embed it via `//go:embed`, and invoke `/usr/bin/python3` via subprocess to obtain up to 0.9695 in `re` fallback mode.
  - **Status:** This vulnerability was reported as an **unverified theoretical hypothesis** and was **not experimentally validated** with a live Harbor exploit run. Per evaluation protocol, we do not claim to have fixed this untested vector.
  - **Proposed Future Hardening:** Set `RUN chmod 0750 /usr/bin/python3*` and `chmod 700 /workspace/repo` in `task/tests/Dockerfile`.

---

## 6. Five-Minute Presentation Outline

1. **Minute 1 — Introduction & Day 4 Vulnerabilities:**
   - Summarize the initial task flaws: leaked visible answers, structural points awarded for empty binaries, and linear accuracy scoring.
   - Highlight Cheat 2 (Half Port) as the most potent cheat (`0.7213`).
2. **Minute 2 — Day 5 Hardening & Ashish's Re-attack:**
   - Explain how removing answer leaks and structural floor eliminated Cheats 1 and 3.
   - Present Ashish's Day 6 finding: Cheat 2 survived at `0.2936` on the 100K exam because linear scoring granted 29.36% of lines for free.
3. **Minute 3 — Day 6 Fixes (Threshold Scoring & Build Context):**
   - Walk through the 90% threshold scoring formula in `task/tests/support.py`.
   - Explain the resolution of the build-context defect by removing `docker-compose.yaml` and vendoring `python-titlecase`.
4. **Minute 4 — Empirical Proof Results:**
   - Present the Harbor proof table: Oracle scores `1.0`, NOP scores `0.0`, and all three attacker cheats score `0.0000`.
   - Highlight that genuine partial credit is preserved above the 90% floor.
5. **Minute 5 — Surprises, Limitations & Takeaways:**
   - Discuss why large datasets alone cannot protect linear scoring models.
   - Acknowledge the unverified Python interpreter hypothesis and outline future container sandbox isolation.
