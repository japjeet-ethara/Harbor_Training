# Day 4 — Attack Report

## Target
- Owner: Shubham Tumane
- Task: titlecase-go
- Target snapshot: See `TARGET.txt`
- Experiments: Python Inside, Half Port, Build Trick

---

## Cheat 1 — Python Inside

### What it does
Uses the original Python titlecase implementation supplied in the task's Docker image instead of implementing the transformation in Go.

The solution:
1. Copies the original Python package from `/workspace/repo/titlecase` to `/tmp/titlecase-python`.
2. Removes `.py` files from `/workspace/repo`.
3. Creates a Go wrapper that invokes the original Python CLI.
4. Builds the Go wrapper successfully.

This is an intentional runtime-language bypass, not a genuine Go implementation.

### Actual result
- Overall reward: 1.0
- Behaviour: 1.0
- Build: 1.0
- No Python: 1.0
- Exceptions: 0

### Job folder
`jobs/2026-11-19__18-39-12`

### Trial folder
`scratch-cheat1__kTLMJAx`

### Why it scored
The Dockerfile installs Python and copies the original Python package into `/workspace/repo`.

Evidence:
- `target/environment/Dockerfile:4-5` installs Python 3 and pip.
- `target/environment/Dockerfile:12` copies `python-titlecase/` into `/workspace/repo/`.
- `target/environment/python-titlecase/titlecase/__init__.py:80` defines the original `titlecase()` implementation.
- `target/environment/python-titlecase/titlecase/__init__.py:241` defines the original CLI function.
- `target/environment/python-titlecase/titlecase/__init__.py:292` shows the CLI invoking `titlecase()` and writing its output.
- `tests/no_python.py:9-24` checks for `.py` files inside the repository and successful Go compilation, but does not check whether the program invokes a Python interpreter at runtime.

The solution moves the package outside the repository before deleting `.py` files. The Go program then invokes Python using the preserved package.

Because the wrapper uses the original implementation, it matches the hidden behaviour dataset while also passing the build and no-Python checks. All three criteria therefore received full credit.

### Suggested fix
Check runtime dependencies and execution behaviour, not just `.py` file extensions inside the repository. Consider evaluating in an environment without Python.

---

## Cheat 2 — Half Port

### What it does
Implements a deliberately simplified Go titlecaser:
- Splits input into whitespace-separated words.
- Capitalizes the first character of ordinary words.
- Keeps selected small words lowercase except at the beginning and end.
- Does not implement the full punctuation, acronym, hyphenation, apostrophe, and other advanced rules.

### Actual result
- Overall reward: 0.7027
- Behaviour: 0.108
- Build: 1.0
- No Python: 1.0
- Exceptions: 0

### Job folder
`jobs/2026-11-18__22-51-25`

### Trial folder
`scratch-cheat2__RcU8uLR`

### Why it scored
The simplified Go program compiled successfully and the Python-file cleanup check passed. It earned only 0.108 behaviour credit, showing limited exact matching against the hidden dataset.

Evidence:
- `tests/build.py:11-18` awards build credit when `go build ./...` succeeds.
- `tests/no_python.py:9-24` awards credit when no `.py` files remain and the Go build succeeds.
- Neither check requires the titlecase output to be correct.

### Suggested fix
Make build and cleanup checks dependent on a meaningful behaviour threshold, or use a pass/fail behaviour gate. Add broader edge-case tests for punctuation, acronyms, contractions, Unicode, and whitespace.

---

## Cheat 3 — Build Trick

### What it does
Creates a minimal Go module with an empty `main()` function, deletes `.py` files, and builds the Go program. It does not implement titlecase conversion.

### Actual result
- Overall reward: 0.6667
- Behaviour: 0.0
- Build: 1.0
- No Python: 1.0
- Exceptions: 0

### Job folder
`jobs/2026-11-18__22-59-14`

### Trial folder
`scratch-cheat3__EFjPQYF`

### Why it scored
The empty Go program received zero behaviour credit but passed both the build and no-Python checks. These independent checks allowed it to receive an overall reward of 0.6667 without implementing the requested functionality.

Evidence:
- `tests/behaviour.py:36-44` compares actual output lines with expected lines and calculates the exact-match score.
- `tests/build.py:11-18` awards build credit based on successful compilation.
- `tests/no_python.py:17-24` awards no-Python credit when there are no `.py` files and compilation succeeds.

### Suggested fix
Gate build and cleanup credit on a minimum behaviour score, or make functional correctness a prerequisite for the overall reward.

---

## Final Comparison

| Experiment | Behaviour | Build | No Python | Overall |
|---|---:|---:|---:|---:|
| Cheat 1 — Python Inside | 1.000 | 1.000 | 1.000 | **1.0000** |
| Cheat 2 — Half Port | 0.108 | 1.000 | 1.000 | 0.7027 |
| Cheat 3 — Build Trick | 0.000 | 1.000 | 1.000 | 0.6667 |

## Highest Score

Cheat 1 — Python Inside: **1.0000**.

