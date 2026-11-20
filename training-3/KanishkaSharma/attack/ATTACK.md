# Attack Report — Target: Ayush Mishra

## Target Info
- Target Name: Ayush Mishra
- Target Commit SHA: 82d1bd1e946f78859cb9739a6f2a7d840e60d379
- Note on Environment: `test.sh` had Windows CRLF line endings; converted to LF in local copy to enable container execution on Linux without altering target logic. Pristine target verifier files (`reward.toml`, `task.toml`, and test scripts) remain 100% unmodified from the official source.

---

## Cheat 1 — Read the Hidden Exam
- **What it does:** The Go solution bypasses normal execution and directly opens `/tests/data/hidden_expected.txt` to dump the exact expected output.
- **Score:** reward 1.00 (`build: 1.0, no_python: 1.0, behaviour: 1.0`)
- **Job folder / ID:** `jobs/2026-11-18__23-37-59`
- **File:Line Evidence:** 
  - `tests/behaviour.py:9-10` (defines hidden expected data paths)
  - `tests/behaviour.py:56-65` (runs agent Go binary in the container context where hidden files reside)
- **Why it worked:** The verifier executes the Go binary inside the container where `/tests/data/hidden_expected.txt` is accessible, allowing the solution to read expected answers directly.
- **How to fix:** Isolate test data completely and restrict file read permissions so the test runner compares dynamically executed outputs without exposing expected answer files to the workspace container.
- **Result file:** `attack/results/cheat1-reward.json`

---

## Cheat 2 — Python Inside
- **What it does:** Renames the original Python `titlecase/__init__.py` into a data file (`engine.dat`) before deleting `.py` files, then runs a Go wrapper that invokes `python3` via `exec.Command` to evaluate titles.
- **Score:** reward 1.00 (`build: 1.0, no_python: 1.0, behaviour: 1.0`)
- **Job folder / ID:** `jobs/2026-11-18__23-39-39`
- **File:Line Evidence:**
  - `tests/no_python.py:13` (scans strictly for `*.py` extensions under workspace)
  - `tests/Dockerfile:6-9` (ensures Python 3 runtime is installed in verifier container)
- **Why it worked:** `tests/no_python.py` only checks for `.py` extensions, so hiding Python code inside `.dat` files and executing via system `python3` binary bypasses the check.
- **How to fix:** Block python binary execution via seccomp/apparmor or perform deeper static/dynamic content inspection during the no-python verification phase.
- **Result file:** `attack/results/cheat2-reward.json`

---

## Cheat 3 — Delete + Empty Build Trick
- **What it does:** Deletes all `.py` files and submits an empty Go program (`func main() {}`) that builds successfully.
- **Score:** reward 0.3333 (`build: 1.0, no_python: 1.0, behaviour: 0.0`)
- **Job folder / ID:** `jobs/2026-11-18__23-41-10`
- **File:Line Evidence:**
  - `tests/reward.toml:4` (defines independent partial weights for build and environment checks)
- **Why it worked:** `tests/reward.toml` awards partial scores independently for successful compilation and environment compliance before behavioral tests execute.
- **How to fix:** Tie build and environment compliance checks strictly to successful behavioral test execution.
- **Result file:** `attack/results/cheat3-reward.json`

---
**Highest score achieved by a cheat:** 1.00
