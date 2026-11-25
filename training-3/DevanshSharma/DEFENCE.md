# DEFENCE.md — Day 6 report
**Defender:** Devansh Sharma  
**Attacker:** Kushal Soni  
**Task:** titlecase-go (stdlib re mode, 100k exam)

---

## Strongest cheat before hardening

Kushal Soni ran three cheats against the original task (commit `58e8de8`):

| Cheat | Description | Reward (before) |
|---|---|---|
| cheat1 — read exam | Reads answer file from disk at run time | **1.0** |
| cheat2 — Python inside | Embeds Python source, shells out to `/usr/bin/python3` | **1.0** |
| cheat3 — half port | Partial Go port, correct on easy/invariant inputs | **0.4862** |

**Strongest cheat:** cheat1 and cheat2 both scored 1.0. cheat1 (read exam) was the most trivial — the answer files were world-readable and the binary ran as root, so the cheat just opened `hidden_expected.txt` and printed it verbatim.

---

## After hardening

| Cheat | Reward (before) | Reward (after) | Job |
|---|---|---|---|
| cheat1 — read exam | 1.0 | **0.1111** | `cheat1c__qzeKsW5` |
| cheat2 — Python inside | 1.0 | **0.0556** | `cheat2c__muxvQ4M` |
| cheat3 — half port | 0.4862 | **0.1111** | `cheat3c__Ljx3M7b` |

Oracle reward after hardening: **1.0** (job in `task/jobs/oracle-h5`)

---

## Exam: before and after

| Property | Old exam | New exam |
|---|---|---|
| Size | 2,000 inputs | 100,000 inputs |
| Mode | default (regex package allowed) | stdlib re only (no `regex` package) |
| Invariant rate | ~15% (many already-cased tokens) | <1% (pool stresses tricky cases) |
| Visible/hidden overlap | ~24% (one RNG, one pool) | 0% (inputs.txt is the full exam; no separate hidden set) |
| Tricky cases included | no | yes: `v1.2`, `_dream`, `v._`, inline-period-with-digit, mixed Unicode |

---

## Fixes applied

**cheat1 — read exam (1.0 → 0.1111)**  
Two changes: `behaviour.py` now `chmod 0600`s the answer files before running the binary, and the binary runs as `su candidate` (a locked-down user created in the Dockerfile with no home directory). As `candidate`, the cheat cannot read the root-owned `0600` files. The residual 0.1111 comes from the build+no_python baseline (2/6 ≈ 0.333) reduced to near zero by the 50% behaviour threshold.

**cheat2 — Python inside (1.0 → 0.0556)**  
Two changes: the verifier Dockerfile switched from `FROM python:3.12-slim` to `FROM golang:1.23` with an explicit `apt-get purge python3*` — no interpreter in the image, so the cheat's embedded `.py` has nothing to run. The `no_python.py` check was also extended to call `uses_exec()`, which rejects any `.go` file importing `os/exec` or `syscall`, blocking the shell-out vector regardless of what's installed.

**cheat3 — half port (0.4862 → 0.1111)**  
The 100k pool contains 90k+ inputs that titlecase always changes (tricky Unicode, version strings, underscore-words, mixed-case abbreviations). A partial port that handles only easy cases gets ~42% behaviour, which falls below the 50% threshold and scores 0 for behaviour. The residual 0.1111 again comes from the baseline components, not from behaviour.

---

## One surprise

The hardest bug to fix was not in the verifier at all — it was in my own Go port. When I regenerated the exam to 100k inputs, the oracle scored **0.8488** instead of 1.0: 15,118 lines wrong. All failures traced to three subtle mismatches between Python's `\w` and Go's `unicode.IsLetter`/`unicode.IsDigit`:

1. Python `\w` includes `_`; Go's letter/digit checks do not. So `_dream` → `_Dream` was wrong.
2. `hasInlinePeriod` used `unicode.IsLetter` to bracket a `.`, missing `v1.2` (digit before `.`).
3. `capFirst` skipped any punctuation character to find the first letter, but `_` is both punctuation (Unicode category) and `\w`, so Python's regex stopped at `_` while Go skipped past it.

Each fix was one line, but finding them required diffing 15k wrong outputs against expected and tracing back through the Python source. The lesson: a small exam can mask systematic bugs; 100k inputs exposed all three independently.
