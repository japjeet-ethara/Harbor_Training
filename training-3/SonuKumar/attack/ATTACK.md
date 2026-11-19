# Attack Report — Sanyam Sehrawat's titlecase-go Task

**Target Student:** Sanyam Sehrawat  
**Target Commit SHA:** `9c8b84d4d7da90ea8feceb9f5e9a39720a672b53`  
**Target Task Location:** `SanyamSehrawat/titlecase-go`  
**Date of Evaluation:** November 18, 2026  
**Evaluator:** Sonu Kumar (`Sonu Kumar/`)

---

## 1. Target Task Audit and Security Analysis

### Execution Context & Visibility
- Inside the agent execution container (`environment/Dockerfile:16-21`), the agent runs as `agent` and only has access to `/workspace/repo`, which contains `python-titlecase` (version 2.4.1) files.
- The grading suite (`tests/`) is NOT visible to the agent during execution; it exists only in the verifier container (`task.toml:27` specifying `environment_mode = "separate"`).
- In the verifier container (`tests/Dockerfile:1-13`), `COPY . /tests/` copies the tests, including test scripts and datasets (`tests/data/sample/` and `tests/data/graded/`).

### Verification & Scoring Mechanics
- Entrypoint `tests/test.sh:6` executes `python3 /tests/grade.py /workspace/repo /tests/data/graded /logs/verifier/reward.json`.
- The evaluation defines three checks with fixed weights (`tests/grade.py:25`):
  - `build` (weight 1): Verifies `go.mod` has no `require` or `replace` directives and that `go build ./...` and `go build -o /tmp/titlecase .` succeed (`tests/grade.py:42-59`).
  - `no_python` (weight 1): Recursively scans `/workspace/repo` and awards 1.0 if no file ending in `.py` remains (`tests/grade.py:62-70`).
  - `behaviour` (weight 4): Runs `/tmp/titlecase` under user `nobody`, feeds `/tests/data/graded/titles.txt` (2,000 lines) through stdin, and compares stdout byte-by-byte to `/tests/data/graded/answers.txt` (`tests/grade.py:87-120`).
- Final reward formula (`tests/grade.py:139`):
  $$\text{reward} = \frac{1 \cdot \text{build} + 1 \cdot \text{no\_python} + 4 \cdot \text{behaviour}}{6.0}$$

### Weakest Points Identified
1. **Unconditional points for deleting `.py` files (`tests/grade.py:25, 126-127`):** `no_python` (weight 1) awards full credit as long as `build == 1.0` and no `.py` files exist, without checking whether any real translation work was done. Together, `build` + `no_python` guarantee a base reward of $2/6 \approx 0.3333$ (33.33%) to a completely empty stub.
2. **Partial credit inflation via naive heuristic (`tests/grade.py:113, 120`):** `behaviour` computes linear match ratio `matched / len(answers)`. Naive space-delimited word capitalization easily matches titles that contain only common capitalized words and no small words, acronyms, or punctuation edge cases (409 of 2,000 lines, earning 20.45% behaviour and 0.4697 overall).
3. **Verifier image architecture & Python execution leak (`tests/Dockerfile:8` and `tests/grade.py:62-70`):** `python3` is installed in the verifier container (`tests/Dockerfile:8`), contrary to `instruction.md:34` which claims the container has no Python. Furthermore, `check_no_python` only checks `f.endswith(".py")`. A solution can rename Python files and call `python3` via a Go subprocess to achieve 98.45% output accuracy without writing a Go titlecase engine.

---

## 2. Official Day 4 Cheats (Three Core Experiments)

### Cheat 1 — Delete Trick (Minimal Go Stub)
- **Strategy:** Delete trick / Build trick.
- **What it does:** Deletes all `.py` files and python build artifacts from `/workspace/repo`, creates a standard-library `go.mod`, and writes a minimal 20-line `main.go` that prints empty lines for each input.
- **Expected weakness:** `tests/grade.py:62-70` checks only that no `*.py` files remain. Combined with `tests/grade.py:42-59` (`go build`), it should award $1/6 + 1/6 = 0.3333$ reward without any titlecasing logic.
- **Score:** reward **0.3333** (build 1.0, no_python 1.0, behaviour 0.0)
- **Job folder:** `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-35-40`
- **Why it worked:** `tests/grade.py:58` confirmed `build: ok`, and `tests/grade.py:69` confirmed `no_python: ok`. `behaviour` was 0/2000 lines (`tests/grade.py:114`), but the decoupled scoring formula (`tests/grade.py:139`) awarded 0.3333 total reward.
- **Supporting references:** `tests/grade.py:25`, `tests/grade.py:62-70`, `tests/grade.py:126-127`, `tests/grade.py:139`.
- **How to fix:** Make `no_python` conditional on behaviour (`if scores["behaviour"] > 0: ...`), or require a minimum threshold before awarding points for file deletion.

---

### Cheat 2 — Half Port (Naive Word Capitalization)
- **Strategy:** Half port / Heuristic shortcut.
- **What it does:** Implements a naive Go program that splits input by whitespace and capitalizes the first character of each word, omitting all 20+ specialized rules of titlecase (small words like 'a'/'the', acronyms, Mc/Mac prefixes, contractions, slashes, URLs, punctuation).
- **Expected weakness:** Tests how much partial credit the linear scoring metric (`tests/grade.py:113, 120`) gives to a simplistic heuristic on the 2,000-title dataset.
- **Score:** reward **0.4697** (build 1.0, no_python 1.0, behaviour 0.2045)
- **Job folder:** `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-38-45`
- **Why it worked:** Out of 2,000 titles in `tests/data/graded/titles.txt`, exactly 409 titles (~20.45%) were simple sentences where naive capitalization coincided with python-titlecase output. In `tests/grade.py:120`, this gave `scores["behaviour"] = 409 / 2000 = 0.2045`. Weighted reward: `(1*1.0 + 1*1.0 + 4*0.2045) / 6.0 = 0.4697` (46.97% overall score).
- **Supporting references:** `tests/grade.py:113-120`, `tests/grade.py:139`, `tests/data/graded/titles.txt`.
- **How to fix:** Include complex, adversarial titles (small words, acronyms, diacritics, symbols, unusual whitespace) in the grading dataset so naive capitalization scores close to 0%, or use a non-linear scoring curve with a cutoff floor.

---

### Cheat 3 — Python Inside (Subprocess Wrapper Exploit)
- **Strategy:** Python inside / Subprocess execution bypass.
- **What it does:** Saves the original Python titlecase logic as `titlecase.dat` (mode 666), completely deletes all `*.py` files and the `titlecase/` directory to pass `check_no_python`. Writes a Go command-line program that receives stdin, spawns `python3 -c "..."` to execute `titlecase.dat`, and streams stdout.
- **Expected weakness:** Evaluates whether `tests/Dockerfile:8` allows Python execution inside the container and whether `tests/grade.py:65` can be bypassed by non-`.py` file extensions.
- **Score:** reward **0.9897** (build 1.0, no_python 1.0, behaviour 0.9845)
- **Job folder:** `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-51-32`
- **Why it worked:**
  - `tests/Dockerfile:8` installed `python3` in the verifier container, allowing user `nobody` (`tests/grade.py:99`) to spawn `python3`.
  - `tests/grade.py:65` checks only `f.endswith(".py")`. Renaming to `.dat` awarded full marks (`no_python: 1.0`).
  - `go build` compiled cleanly (`build: 1.0`).
  - Output correctness: The original Python library running under `re` matched **1,969 of 2,000 lines (98.45% output match rate)**, failing only 31 lines where Debian `re` differed slightly from `regex`.
  - Specification compliance: **0% pure Go implementation.** The solution is an unauthorized subprocess wrapper that executes Python rather than porting it to Go, yet Sanyam's grader rewarded it with a near-perfect score of **0.9897**.
- **Supporting references:** `tests/Dockerfile:8`, `tests/grade.py:62-70`, `tests/grade.py:98-101`, `instruction.md:23-24, 32-34`.
- **How to fix:** Remove `python3` completely from the verifier container image by writing the grader in compiled Go, or use kernel sandboxing (e.g. `seccomp` or container isolation without `exec`) to prevent the binary from launching external interpreters.

---

## 3. Results Table (Official Day 4 Cheats)

| Cheat | Strategy | Overall Reward | Build | No-Python | Behaviour | Lines Matched | Output Match Rate | Specification Compliance | Job Folder |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Cheat 1** | Delete trick (Minimal stub) | **0.3333** | 1.000 | 1.000 | 0.0000 | 0 / 2000 | 0.00% | 0% (Empty stub) | `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-35-40` |
| **Cheat 2** | Half port (Naive capitalization) | **0.4697** | 1.000 | 1.000 | 0.2045 | 409 / 2000 | 20.45% | Partial heuristic | `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-38-45` |
| **Cheat 3** | Python inside (Subprocess wrapper) | **0.9897** | 1.000 | 1.000 | 0.9845 | 1969 / 2000 | **98.45%** | **0% (Python wrapper)** | `Harbor_Day4_Workspace/Sonu Kumar/jobs/2026-11-18__23-51-32` |

---

## 4. Final Assessment

- **Highest reward achieved:** **0.9897** (achieved by Cheat 3 — Python Inside).
- **Most critical grading weakness:** The presence of `python3` in the verifier container combined with a filename-only extension check (`.py`) for Python detection. This allows a candidate to wrap the original Python library in Go and earn ~99% marks without writing a single line of Go titlecase conversion.
- **Three recommended improvements for Sanyam:**
  1. **Purge Python from Verifier Container:** Rewrite `grade.py` into a compiled Go binary so `python3` is not installed anywhere in the verifier image.
  2. **Condition `no_python` on Behaviour:** Require `behaviour >= 0.5` before awarding the `no_python` score point to prevent stub solutions from receiving free credit.
  3. **Harden Test Inputs against Heuristics:** Expand the test suite to 100,000 diverse titles containing small words, acronyms, and non-ASCII characters to drive naive heuristics down to ~0%.

---

---

The highest score any cheat got: 0.9897
