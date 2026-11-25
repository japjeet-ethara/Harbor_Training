# HARDEN.md — Day 5 Report

Task: `ShashwatSuman/task`  
Target / Attacker: Ansh Dixit  
Commit Attacked: `dcbe88466f7281cfb7969a6ff9288f2be331de32`

---

## Holes Closed

### Cheat 1: Read the exam at run time
- **Was:** 1.0 (build 1, no_python 1, behaviour 1.0)
- **Now:** 0.000000 (job/eval: `jobs-local/cheat1-harden`)
- **Fix:** Pre-load all answers in Python memory and hash them with SHA-256 before running the candidate Go binary. Candidate binary runs in an isolated temporary sandbox (`/tmp/run_sandbox`) without access to `/tests/data/`. In the verifier Dockerfile, `/tests` permissions are restricted to `700`.

### Cheat 2: Python inside
- **Was:** 1.0 (build 1, no_python 1, behaviour 1.0)
- **Now:** 0.012195 (job/eval: `jobs-local/cheat2-harden`)
- **Fix:** `no_python.py` was hardened to inspect all non-Go text files for Python source patterns (`import sys`, `import os`, `def titlecase(`, `#!/usr/bin/env python`). Furthermore, Go source files are scanned to prohibit `os/exec` invocations of Python interpreters. In `Dockerfile`, `/opt/uv-tools` and `/opt/uv-python` are restricted (`chmod 700`).

### Cheat 3: Delete trick + empty program
- **Was:** 0.3333 (build 1, no_python 1, behaviour 0.0)
- **Now:** 0.024390 (job/eval: `jobs-local/cheat3-harden`)
- **Fix:** In `reward.toml`, reweighted the checks to `{ build = 0.05, no_python = 0.05, behaviour = 4.0 }`. An empty stub that does nothing receives only `(0.05 + 0.05) / 4.10 ≈ 0.024`, which is well below the 0.20 ceiling.

---

## Exam: Before and After

- **Old exam:** 2,000 synthetic inputs, mode: unstated
- **New exam:** 100,000 unique titles from fixed seed 1 (`make_pool.py 100000 1 pool.txt`), answers frozen twice with `answers.py`, mode explicitly stated in `instruction.md`: **WITH regex**.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
| :--- | :--- | :--- | :--- |
| **my-oracle** (`ShashwatSuman`) | 0 of 100,000 | n/a | 100% |
| **RamandeepSingh** | 0 of 100,000 | no | 100% |
| **VishuPorwal** | 3,053 of 100,000 | no | 0% |
| **AmanEthara** | 2,543 of 100,000 | no | 0% |

*(Measurement output files preserved in `measure/my-oracle.txt`, `measure/RamandeepSingh.txt`, `measure/VishuPorwal.txt`, and `measure/AmanEthara.txt`)*

---

## What I Learned
1. **Inputs matter more than count, but size exposes edge cases**: Rare constructs like `v1.2`, `Mcx-`, non-breaking spaces, and tabs reveal mode incompatibilities (3,053 differences between `re` and `regex` ports).
2. **Never execute candidate binaries in the exam room**: Running an untrusted binary inside the same container directory where test answer files exist completely breaks test integrity unless filesystem access is sandboxed and answers are pre-hashed.
3. **Weight cheap checks proportionally**: Giving independent unit test points for trivial conditions like `go build` and file deletion invites empty stubs unless gated by behaviour score or weighted down to negligible percentages.
