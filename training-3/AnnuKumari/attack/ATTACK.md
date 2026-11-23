# Attack Report — Shivam Tiwari (`titlecase-go`)

Target: Shivam Tiwari (`8a12385d0284da21ba6478497c37ed3bd630db16`)

## Cheat 1 — Python inside
What it does:   Copies `titlecase/__init__.py` to `py_engine.txt`, deletes all `.py` files, and embeds the Python code in Go via `//go:embed`. At runtime, the Go binary passes stdin to `/usr/local/bin/python3 -c` instead of implementing titlecase in Go.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-19__14-54-00
Why it worked:  `tests/no_python.py:17` only checks `name.endswith(".py")` in `/workspace/repo`, while `tests/Dockerfile:1` uses `FROM python:3.12-slim` so `/usr/local/bin/python3` remains executable at runtime.
How to fix:     Use a Python-free verifier image (`golang:1.23`), ban `os/exec` and `syscall` imports in Go, and scan binaries/assets for embedded Python signatures.

## Cheat 2 — Half port
What it does:   Deletes all `.py` files and writes a minimal Go capitalizer that only splits on spaces/tabs and lowercases basic small words. It skips apostrophes, `Mc`/`Mac`, honorifics, inline periods, acronyms, slashes, hyphens, and subphrase punctuation.
Score:          reward 0.453  (build 1, no_python 1, behaviour 0.1795)
Job folder:     jobs/2026-11-19__14-51-41
Why it worked:  `tests/behaviour.py:37-38` awards linear partial credit (`matches / len(expected)`) with no edge-case gating, and `tests/gen.py:204` weights simple `normal()` words 3x higher than edge cases.
How to fix:     Gate partial credit behind minimum overall and edge-case accuracy thresholds, and increase the density of tricky edge cases in the hidden exam.

## Cheat 3 — Delete trick + public notes lookup
What it does:   Deletes all `.py` files and compiles a tiny Go map lookup containing only the 23 example lines from `NOTES.md`, echoing unknown lines unchanged. It implements zero titlecase logic.
Score:          reward 0.3883  (build 1, no_python 1, behaviour 0.0825)
Job folder:     jobs/2026-11-19__14-56-31
Why it worked:  `tests/build.py:14-16` and `tests/no_python.py:23-27` award `2/6` (`0.3333`) points unconditionally for compiling any stub after deleting `.py` files, and `tests/gen.py:19-43, 238-239` leaks 104 `NOTE_LINES` into `hidden_inputs.txt`.
How to fix:     Require non-trivial `behaviour` accuracy before awarding `build` or `no_python` points, and ensure zero overlap between public examples and hidden test inputs.

Highest score any cheat got: 1.0
---

## Day 6 Re-Attack (After Hardening)
Re-ran all three cheats against Shivam Tiwari's hardened task (`training-3/ShivamTiwari/task`):

| Cheat | Score After Hardening | Job Folder | Status |
|-------|----------------------:|------------|--------|
| Cheat 1 (Python inside) | `0.000` | `jobs/2026-11-23__10-46-56` | Blocked |
| Cheat 2 (Half port) | `0.0052` | `jobs/2026-11-23__10-47-55` | Blocked |
| Cheat 3 (Delete trick + public notes lookup) | `0.0022` | `jobs/2026-11-23__10-48-45` | Blocked |

All three exploits are now closed and score well below `0.2`.
