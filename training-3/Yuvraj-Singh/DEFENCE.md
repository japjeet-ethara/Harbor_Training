# Day 6 Presentation & Defence Notes — Yuvraj Singh (titlecase-go)

**Presenter:** Yuvraj Singh  
**Task:** `titlecase-go`  
**Time Limit:** 5 Minutes  

---

## 1. Strongest Cheat Against My Task

### The Attack (Paniv Kapoor — Cheat 2)
* **Strategy:** Python hidden in an extensionless file (`py_titlecase_engine`) and invoked via Go's `os/exec` command (`exec.Command("python3", ...)`).
* **Before Score:** **`1.0000`** (Perfect score on Day 4 — Job: `jobs/2026-11-18__18-28-10`).
* **After Hardening:** **`0.0625`** (Hard failure on Day 6 — Job: `jobs/2026-11-20__17-44-44`).

### Why It Succeeded Originally
1. `tests/no_python.py` only scanned for files matching the pattern `*.py`. The extensionless file bypassed the filename glob completely.
2. Python was available inside the container runtime environment, so `python3 py_titlecase_engine` executed without errors.
3. The Go wrapper proxied stdin to Python, passing 100% of behavior tests with the genuine Python library.

### How I Closed It
1. **Removed Python completely from the environment and verifier containers:**
   * In `environment/Dockerfile`: `rm -rf /usr/bin/python* /usr/local/bin/python* /usr/lib/python*`.
   * In `tests/Dockerfile`: Purged default Debian Python from the verifier image.
2. **Multi-layer AST and byte inspection in `tests/no_python.py`:**
   * Rejects files with Python shebangs (`#!/usr/bin/env python`, etc.).
   * Scans Go sources for subprocess execution strings (`"python"`, `"python3"`, `` `python` ``).
3. **Behavior Gating in `tests/behaviour.py`:**
   * If any `.py` file remains or Python tampering is detected, `behaviour` immediately returns `0.0`.

---

## 2. Before-and-After Exam Comparison

### Exam Evolution
* **Old Exam:** 2,000 hidden test inputs with basic ASCII titles.
* **New Exam:** 100,000 titles generated with seed 1 via `kit/make_pool.py`, frozen with `kit/answers.py` using `python -I` (without regex).
* **Reference Mode:** Explicitly specified in `instruction.md` as **WITHOUT regex**.

### Port Evaluation Comparison

| Port | Wrong on New 100k Exam | Caught by Old 2k Exam? | Chance 2k Exam Misses Bug |
| :--- | :---: | :---: | :---: |
| **My Oracle (`solution/solve.sh`)** | **0** | n/a (passed) | n/a |
| **Classmate Port A** | **857** | No | **0%** |
| **Classmate Port B** | **16** | No | **72%** |

### Proof of Hardening

| Run | Required Threshold | Hardened Score | Job Directory | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Oracle** | `1.000` | **1.000** | `jobs/2026-11-20__17-45-11` | PASS |
| **Nop** | `0.000` | **0.000** | `jobs/2026-11-20__17-47-42` | PASS |
| **Paniv Cheat 1** | `< 0.200` | **0.125** | `jobs/2026-11-20__17-44-29` | PASS |
| **Paniv Cheat 2** | `< 0.200` | **0.062** | `jobs/2026-11-20__17-44-44` | PASS |
| **Paniv Cheat 3** | `< 0.200` | **0.125** | `jobs/2026-11-20__17-44-57` | PASS |

---

## 3. Surprising Discoveries

1. **The Verifier Container Subshell Leak in Separate Mode:**
   In Harbor's `separate` environment mode, binaries run inside the verifier container (`task/tests/Dockerfile`) during evaluation. Even though we purged Python from the user's environment container, the compiled Go binary could still execute `/usr/bin/python3` if the verifier container had Python installed. True containment required stripping Python from *both* Dockerfiles.

2. **The "Weighted-Mean" Grading Trap vs. Behavioral Gating:**
   If checks are combined with a simple weighted mean without gates, an attacker can leave Python files behind and still score `13/14 = 0.9286` (A-grade). Hard-gating behavior on the absence of Python files drops the attacker's score straight to `0.0625` without needing artificial weight inflation.

3. **The 3,053-Line Divergence (Lesson 3):**
   Depending on whether Python's third-party `regex` library is installed, standard `titlecase()` outputs 3,053 different titles out of 100,000. When attacking Prashant Kumar's hardened task, we discovered an exam discrepancy where his `instruction.md` specified "WITHOUT regex", but his hidden test answers were generated *with* `regex`. This reinforced the critical lesson of stating and strictly matching the frozen reference implementation mode.
