# Attack Report

**Target:** Ramandeep Singh's `titlecase-go` task  
**Commit SHA:** `616287a` (branch `training-3`)  
**Attacker:** Shashwat Suman  

---

## Task Vulnerability Analysis

A detailed inspection of Ramandeep Singh's task files (`tests/test.sh`, `tests/behaviour.py`, `tests/build.py`, `tests/no_python.py`, `tests/reward.toml`, `tests/Dockerfile`) reveals several critical vulnerabilities:

1. **Direct Access to Hidden Verification Data (`tests/behaviour.py:23-28`)**:
   `tests/behaviour.py` references `/tests/data/hidden_expected.txt` which is copied into the evaluation image root filesystem (`tests/Dockerfile:9` -> `COPY . /tests/`). Because the candidate program runs in the same container without filesystem sandboxing, it can read `/tests/data/hidden_expected.txt` directly.

2. **Python Runtime Available in Verifier Container (`tests/Dockerfile:1`)**:
   The verification container base image is `python:3.12-slim`. The `no_python` check (`tests/no_python.py:21-25`) merely performs a static check for files ending in `.py`. It does not prevent runtime execution of Python or non-`.py` Python code (e.g., executing `python3 -c ...` on a renamed reference file).

3. **Unearned Credit for Build and No-Python (`tests/reward.toml:4`)**:
   The reward calculation assigns equal weights to `build` (1.0) and `no_python` (1.0) alongside `behaviour` (4.0). A completely empty Go stub that does nothing receives `2.0 / 6.0 = 0.333333` (33.3% of total score) without producing even a single correct title.

4. **Small & Non-Diverse Exam (`tests/data/hidden_inputs.txt`)**:
   The exam consists of only 2,000 synthetic lines generated from the same deterministic random seed (`gen.py:13` `random.seed(1)`). It lacks edge cases such as `Mcx-`, non-breaking spaces, or Turkish characters.

---

## Cheat 1 — Direct Hidden Expected Output Access

**What it does:**  
Instead of implementing any Go titlecase logic, the candidate program simply reads `/tests/data/hidden_expected.txt` directly from disk and streams it to standard output. It deletes `.py` files and compiles a valid Go program.

**Score:**  
- **Reward:** 1.000000  
- **Build:** 1.0  
- **No_Python:** 1.0  
- **Behaviour:** 1.0  

**Job folder:**  
`jobs/2026-11-18__18-34-34`

**Trial:**  
`titlecase-go__FYGv8nL`

**Reward file:**  
`results/cheat1-reward.json`

**Why it worked:**  
In `tests/behaviour.py` lines 23-28 and 59-65, the candidate binary is executed via `subprocess.run([str(bin_path)])` without filesystem isolation or permission barriers. The file `/tests/data/hidden_expected.txt` is world-readable inside the container.

**How to fix:**  
Do not place hidden verification answers inside the candidate's execution environment. Isolate the candidate process using a restricted sandbox or container with read-only stdin and no access to test data directories.

---

## Cheat 2 — Python Inside Go Wrapper

**What it does:**  
Preserves the reference implementation by copying `titlecase/__init__.py` to `reference.txt` before deleting all `.py` files. The Go binary invokes `python3 -c ...` to execute the Python reference code at runtime, matching 100% of the behaviour.

**Score:**  
- **Reward:** 1.000000  
- **Build:** 1.0  
- **No_Python:** 1.0  
- **Behaviour:** 1.0  

**Job folder:**  
`jobs/2026-11-19__11-41-44`

**Trial:**  
`titlecase-go__Bkpq5it`

**Reward file:**  
`results/cheat2-reward.json`

**Why it worked:**  
`tests/no_python.py` lines 21-25 only search for filenames matching `*.py` under `/workspace/repo`. Because `python3` is installed in the container (`tests/Dockerfile:1`), the Go binary can launch Python to run arbitrary scripts disguised as non-`.py` text files.

**How to fix:**  
Ensure Python is not installed in the execution environment or remove Python binaries prior to testing. Additionally, inspect running processes or disallow subprocess execution.

---

## Cheat 3 — Build Trick / Delete Trick (Unearned Partial Credit)

**What it does:**  
Compiles a minimal dummy Go program that simply echoes standard input unmodified and deletes `.py` files. It performs zero transformation logic.

**Score:**  
- **Reward:** 0.333333  
- **Build:** 1.0  
- **No_Python:** 1.0  
- **Behaviour:** 0.0  

**Job folder:**  
`jobs/2026-11-16__18-31-26`

**Trial:**  
`titlecase-go__hYXkC4C`

**Reward file:**  
`results/cheat3-reward.json`

**Why it worked:**  
`tests/reward.toml` defines a weighted mean with weights `{ build = 1.0, no_python = 1.0, behaviour = 4.0 }`. Because `build` and `no_python` have no dependency on `behaviour`, the stub receives `(1.0 + 1.0 + 0) / 6.0 = 0.333333` reward.

**How to fix:**  
Gate `build` and `no_python` marks on achieving a minimal threshold on `behaviour` (e.g. `behaviour > 0.5`), or reduce the weights of `build` and `no_python` to 0.

---

## Summary

- **Highest score achieved by any cheat:** **1.000000** (Full credit via Cheat 1 and Cheat 2).
- The task's exam can be completely bypassed without implementing the titlecase algorithm in Go.
