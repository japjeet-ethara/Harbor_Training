# Attack Report — Sanyam Sehrawat's titlecase-go Task

## 1. Target Overview

- **Attacker:** Sonu Kumar (`Sonu Kumar/`)
- **Defender:** Sanyam Sehrawat (`training-3/SanyamSehrawat/`)
- **Task:** `titlecase-go`
- **Original Day 4 Target Commit:** `9c8b84d4d7da90ea8feceb9f5e9a39720a672b53`
- **Day 6 Hardened Target Commit:** `565b9633ff31580a04062dd8263fd6baa047eeb7`
- **Target Task Directory:** `training-3/SanyamSehrawat/task/`
- **Evaluation Environment:** Harbor 0.25.0 (`golang:1.23`, Docker / Ubuntu WSL)

---

## 2. Three Official Re-Attack Cheats

The three official Day 4 attack cheats were evaluated unmodified against Sanyam's hardened task using Harbor:

| Cheat | Technique | Day 4 Reward | Hardened Reward | Harbor Job Directory | Result Breakdown (`build` / `no_py` / `behav`) | Status |
|---|---|:---:|:---:|---|---|:---:|
| **Cheat 1** | Delete + Echo | 0.3333 | **0.1667** | `jobs/2026-11-20__17-05-28` | `1.0` / `0.0` / `0.0` | Suppressed (< 0.20) |
| **Cheat 2** | Naive Half-Port | 0.4697 | **0.1667** | `jobs/2026-11-20__18-00-30` | `1.0` / `0.0` / `0.0` | Suppressed (< 0.20) |
| **Cheat 3** | Python Wrapper | 0.9897 | **0.0000** | `jobs/2026-11-20__18-02-27` | `0.0` / `0.0` / `0.0` | Eliminated (< 0.20) |

### Technical Analysis of Suppression
- **Cheat 1 (Delete + Echo):** In Day 4, removing all `.py` files unconditionally awarded 1.0 for `no_python` (`tests/grade.py:62-70`), granting $(1 + 1 + 0)/6 = 0.3333$ reward without titlecasing logic. In Day 6, `tests/grade.go:98-101` made `no_python` conditional on `behaviour >= 0.5`. Because the stub produces no matching lines, `no_python` is strictly zeroed, leaving only compilation credit ($1/6 \approx 0.1667$).
- **Cheat 2 (Naive Half-Port):** In Day 4, basic whitespace-splitting and initial-character capitalization matched 409 of 2,000 simple titles (20.45%), yielding a reward of 0.4697 under linear grading. In Day 6, `tests/grade.go:163-166` introduced a 95% qualification cliff (`if ratio < 0.95 { return 0 }`). Matching $< 95\%$ on the 100K exam zeroes behaviour and gates out `no_python`, capping reward at 0.1667.
- **Cheat 3 (Python Wrapper):** In Day 4, renaming the library to `titlecase.dat` and spawning `python3` via `os/exec` scored 0.9897. In Day 6, `tests/grade.go:24-26, 62-66` statically inspects source files for forbidden imports matching `os/exec|syscall|plugin|unsafe|C|net`, rejecting compilation (`build: 0.0`) and cascading to a total reward of 0.0000. Additionally, Python was removed from the container image.

---

## 3. New Cheat 4 — Diagnostic Investigation

Cheat 4 was conducted as an additional experimental investigation to test whether substantial functional titlecase compliance could break the 0.20 suppression threshold under Policy B. It is documented as a diagnostic probe, **not as a successful exploit**.

### Experiment A — Initial Partial Port
- **Technique:** Implemented whitespace tokenization, small-word lookups, and basic titlecasing.
- **Standard LF Output (`jobs/2026-11-20__18-18-53`):**  
  Produced 100,000 lines; verifier recorded **`0 / 100,000 matches`** (Reward: **`0.1667`**).
- **Diagnostic CRLF Output (`jobs/2026-11-20__18-59-07`):**  
  Produced 100,000 lines; verifier recorded **`33,673 / 100,000 matches`** (Reward: **`0.1667`**).
- **Observation:** Emitting CRLF line endings restored 33,673 matching lines (33.67% accuracy) without altering titlecase logic, uncovering a verifier line-ending defect.

### Experiment B — Advanced Deep Partial Port
- **Technique:** Comprehensive standard-library Go engine incorporating `regexp` rules for small words, Mc/Mac prefixes (`McGraw-Hill`), apostrophe handling (`d'Angelo`), inner-capitalization preservation, and hyphen/slash subphrase processing, emitting CRLF lines.
- **Harbor Job Directory:** `jobs/2026-11-20__23-56-52` (Trial: `sanyam-cheat4-deep__7urPztV`, Runtime: 1m 43s)
- **Authentic Verifier Output:**
  - `build: ok` (Score: **1.0**)
  - `behaviour: 48215 of 100000 lines match (100000 lines produced)`
  - `behaviour: below hardened 95% threshold` (Score: **0.0**)
  - `no_python: behaviour threshold not met` (Score: **0.0**)
  - Final Reward: **`0.1667`**
- **Raw Accuracy:** **48.215%** (48,215 of 100,000 lines matched).

## 4. Critical Grader Findings

### A. 95% Behaviour Cutoff (`tests/grade.go:163-166`)
In `tests/grade.go:163-166`, the verifier enforces an all-or-nothing step cutoff:
```go
ratio := float64(matched) / float64(len(answers))
if ratio < 0.95 {
    fmt.Println("behaviour: below hardened 95% threshold")
    return 0
}
```
This contradicts `instruction.md:71-72` (which promises proportional credit based on the "share of hidden input lines") and completely zeroes legitimate partial solutions achieving up to 94.9% accuracy.

### B. No-Python Dependency on Behaviour (`tests/grade.go:98-101`)
In `tests/grade.go:98-101`, `checkNoPython` withholds file-deletion credit unless behaviour reaches 0.5:
```go
if behaviour < 0.5 {
    fmt.Println("no_python: behaviour threshold not met")
    return 0
}
```
This undisclosed gate ensures that any candidate failing the 95% behaviour cutoff also receives 0.0 for `no_python`, even if all `.py` files have been removed.

### C. CRLF Verifier Defect (`tests/grade.go:117`)
- **Root Cause:** In Git commit `565b963`, `task/tests/data/graded/answers.txt` was committed with Windows CRLF (`\r\n`) line endings across all 100,000 lines, protected from Git translation by `tests/data/** -text` in `.gitattributes:3`.
- **Grader Flaw:** In `tests/grade.go:117`, `bytes.Split(bytes.TrimSuffix(rawAnswers, []byte("\n")), []byte("\n"))` splits only on `\n` without stripping `\r`. Consequently, every answer slice retains a trailing `0x0D` (`\r`).
- **Impact:** In `tests/grade.go:157`, `bytes.Equal(produced[i], want)` compares candidate output against `want`. Standard POSIX programs output LF lines, so slices without `\r` fail comparison on 100% of lines.

### D. Genuine Reference Oracle Failure (`jobs/2026-11-20__18-57-24`)
When Sanyam's authentic, untouched reference Oracle (`task/solution/solve.sh`) was evaluated in Harbor:
- **Matches:** **`0 / 100,000 lines match`**
- **Criterion Scores:** `build: 1.0`, `no_python: 0.0`, `behaviour: 0.0`
- **Awarded Reward:** **`0.1667`**
- **Explanation:** Sanyam's Oracle complies with `instruction.md:20-21` by printing standard LF lines via `fmt.Println`. Because the verifier expects CRLF lines, `bytes.Equal` failed on all 100,000 lines, causing the hardened verifier to reject its own reference implementation.

### E. Mathematical Scoring Analysis
The scoring formula implemented in `tests/grade.go:181` is:
$$\text{Reward} = \frac{\text{Build} + \text{NoPython} + 4 \times \text{Behaviour}}{6.0}$$

Under the observed criterion gates, the possible reward ranges are:
1. `Reward = 0.0000`: Build failure or forbidden imports.
2. `Reward = 0.1667`: Build succeeds, but accuracy is below 95% (`Behaviour = 0.0`, `NoPython = 0.0`).
3. `Reward in [0.8000, 0.8333]`: Accuracy is $\ge 95\%$, but `.py` files remain in the repository (`NoPython = 0.0`).
4. `Reward in [0.9667, 1.0000]`: Accuracy is $\ge 95\%$, and all `.py` files have been removed (`NoPython = 1.0`).

**Qualification:** Under these specific criterion gates, ordinary candidates achieving below 95% accuracy are strictly capped at `0.1667`. The gap between 0.1667 and 0.8000 is unreachable through partial behavioral accuracy.

---

