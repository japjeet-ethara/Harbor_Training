# Attack Report — Sanyam Sehrawat's titlecase-go Task

**Target Student:** Sanyam Sehrawat  
**Target Commit SHA:** `9c8b84d4d7da90ea8feceb9f5e9a39720a672b53`  
**Target Task Location:** `SanyamSehrawat/titlecase-go`  
**Date of Evaluation:** November 18, 2026  
**Evaluator:** Sonu Kumar (`SonuKumar/`)

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
2. **Partial credit inflation via naive heuristic (`tests/grade.py:113, 120`):** `behaviour` computes linear match ratio `matched / len(answers)`. Naive space-delimited word capitalization easily matches titles that contain only common capitalized words and no small words, acronyms, or punctuation edge cases.
3. **Verifier image architecture (`tests/Dockerfile:8, 13` and `tests/grade.py:95-99`):** `python3` is installed in the verifier container, and `answers.txt` is stored on the verifier container filesystem. Sanyam relies on `os.chmod('/tests', 0o700)` and `runuser -u nobody` to block reads, which relies strictly on Linux DAC permissions inside the container rather than container isolation.

---

## 2. Cheat Experiments and Verified Harbor Results

### Cheat 1 — Delete Trick (Minimal Go Stub)
- **Strategy:** Delete trick / Build trick.
- **What it does:** Deletes all `.py` files and python build artifacts from `/workspace/repo`, creates a standard-library `go.mod`, and writes a minimal 20-line `main.go` that prints empty lines for each input.
- **Expected weakness:** `tests/grade.py:62-70` checks only that no `*.py` files remain. Combined with `tests/grade.py:42-59` (`go build`), it should award $1/6 + 1/6 = 0.3333$ reward without any titlecasing logic.
- **Score:** reward **0.3333** (build 1.0, no_python 1.0, behaviour 0.0)
- **Job folder:** `SonuKumar/jobs/2026-11-18__18-04-40`
- **Why it worked:** `tests/grade.py:58` confirmed `build: ok`, and `tests/grade.py:69` confirmed `no_python: ok`. `behaviour` was 0/2000 lines (`tests/grade.py:114`), but the decoupled scoring formula (`tests/grade.py:139`) awarded 0.3333 total reward.
- **Supporting references:** `tests/grade.py:25`, `tests/grade.py:62-70`, `tests/grade.py:126-127`, `tests/grade.py:139`.
- **How to fix:** Make `no_python` conditional on behaviour (`if scores["behaviour"] > 0: ...`), or require a minimum threshold before awarding points for file deletion.

---

### Cheat 2 — Half Port (Naive Word Capitalization)
- **Strategy:** Half port / Heuristic shortcut.
- **What it does:** Implements a naive Go program that splits input by whitespace and capitalizes the first character of each word, omitting all 20+ specialized rules of titlecase (small words like 'a'/'the', acronyms, Mc/Mac prefixes, contractions, slashes, URLs, punctuation).
- **Expected weakness:** Tests how much partial credit the linear scoring metric (`tests/grade.py:113, 120`) gives to a simplistic heuristic on the 2,000-title dataset.
- **Score:** reward **0.4697** (build 1.0, no_python 1.0, behaviour 0.2045)
- **Job folder:** `SonuKumar/jobs/2026-11-18__18-06-48`
- **Why it worked:** Out of 2,000 titles in `tests/data/graded/titles.txt`, exactly 409 titles (~20.45%) were simple sentences where naive capitalization coincided with python-titlecase output. In `tests/grade.py:120`, this gave `scores["behaviour"] = 409 / 2000 = 0.2045`. Weighted reward: `(1*1.0 + 1*1.0 + 4*0.2045) / 6.0 = 0.4697` (46.97% overall score).
- **Supporting references:** `tests/grade.py:113-120`, `tests/grade.py:139`, `tests/data/graded/titles.txt`.
- **How to fix:** Include complex, adversarial titles (small words, acronyms, diacritics, symbols, unusual whitespace) in the grading dataset so naive capitalization scores close to 0%, or use a non-linear scoring curve with a cutoff floor.

---

### Cheat 3 — Read the Exam (Hidden Answer Extraction Attempt)
- **Strategy:** Read the exam / Sandbox boundary evaluation.
- **What it does:** At runtime, attempts to open and read `/tests/data/graded/answers.txt` or `/tests/data/sample/answers.txt` from disk to build an exact lookup map; falls back to naive word capitalization if file reading fails.
- **Expected weakness:** Tests whether Sanyam's filesystem permission defense (`os.chmod('/tests', 0o700)` and `runuser -u nobody`) effectively isolates the answer sheet from the executing binary.
- **Score:** reward **0.4697** (build 1.0, no_python 1.0, behaviour 0.2045)
- **Job folder:** `SonuKumar/jobs/2026-11-18__18-08-23`
- **Why it worked or failed:** Sanyam's DAC permission defense **held successfully against file reading**. In `tests/grade.py:95`, `os.chmod` restricted `/tests` to root (mode 0700). Because `/tmp/titlecase` executes under user `nobody` (`tests/grade.py:99`), attempts to open `/tests/data/graded/answers.txt` were denied by the Linux kernel. The binary gracefully fell back to naive capitalization, achieving the same 409 matches (0.2045 behaviour) and 0.4697 reward as Cheat 2.
- **Supporting references:** `tests/grade.py:93-101`, `tests/Dockerfile:13`.
- **How to fix:** While DAC permissions currently block direct access, housing test answers on the same filesystem as untrusted code creates potential escalation risks. A cleaner approach is to execute the binary in an isolated container that receives input via stdin from the outside harness.

---

## 3. Comparative Results Table

| Cheat | Strategy | Overall Reward | Build | No-Python | Behaviour | Job Folder |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Cheat 1** | Delete trick (Minimal stub) | **0.3333** | 1.000 | 1.000 | 0.0000 | `SonuKumar/jobs/2026-11-18__18-04-40` |
| **Cheat 2** | Half port (Naive capitalization) | **0.4697** | 1.000 | 1.000 | 0.2045 | `SonuKumar/jobs/2026-11-18__18-06-48` |
| **Cheat 3** | Read the exam (Answer read attempt) | **0.4697** | 1.000 | 1.000 | 0.2045 | `SonuKumar/jobs/2026-11-18__18-08-23` |

---

## 4. Final Assessment

- **Highest reward achieved:** **0.4697** (achieved by Cheat 2 and Cheat 3).
- **Weakest grading component:** The scoring formula decoupling `build` and `no_python` from `behaviour`, which hands out a free 33.3% score to empty code, combined with a test pool where 20.45% of inputs can be satisfied by naive first-letter capitalization.
- **Three recommended improvements for Sanyam:**
  1. **Condition `no_python` on Behaviour:** Require `behaviour >= 0.5` before awarding the `no_python` score point to prevent stub solutions from receiving free credit.
  2. **Expand and Harden Test Titles:** Expand the test suite to 100,000 diverse titles containing small words, acronyms, and non-ASCII characters to drive naive heuristics down to ~0%.
  3. **Decouple Test Data from Container Filesystem:** Feed inputs and collect outputs strictly via standard streams across isolated container boundaries rather than storing answers on disk next to the running binary.

The highest score any cheat got: 0.4697
