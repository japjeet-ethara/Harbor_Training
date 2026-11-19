# Day 6 — Defence Notes

## 1. The Strongest Cheat Against My Task

- **Strongest cheats:** Cheat 1 (Read the exam) and Cheat 2 (Python inside) by Mohammad Adnan. Both scored a perfect **1.0** on my practice task with no titlecase Go logic at all.
- **Cheat 1 mechanism:** The grader ran the agent's binary inside the verifier container, as root, where `tests/Dockerfile` had copied `tests/data/hidden_expected.txt`. The binary opened that file and printed it line by line.
- **Cheat 2 mechanism:** It renamed `titlecase/__init__.py` to a `.txt`, embedded it in a Go wrapper and ran it with `python3`. `no_python` only looked for files named `*.py`, and the verifier image (`python:3.12-slim`) has `python3`.
- **Before score:** `1.0` for both (attacker's jobs `jobs/2026-11-18__14-54-11` and `jobs/2026-11-18__14-57-36`; my own re-run gave the same 1.0).
- **After hardening score:** `0.1667` for both (build 1.0, no_python 0.0, behaviour 0.0). Jobs: `jobs/2026-11-19__17-49-45` and `jobs/2026-11-19__17-50-58`.
- **The fix** (`tests/checks/port_runner.py`):
  1. The grader reads the answers into memory first.
  2. It copies the compiled binary alone into an empty folder and runs it with `chroot` as user `nobody`, with no environment. Inside there is no `/tests`, no answer file, no `python3` and no shell.
  3. `/tests` is readable by root only (`chmod -R go-rwx /tests` in `tests/Dockerfile` and `tests/test.sh`).
  4. `no_python` pays only if the build passes, no Python is left in any form, and the port gets at least 80% of the hidden answers right.
- **A hole I found myself:** after closing these, I attacked my own task again. Downloading the hidden answers from the public GitHub repo at solve time scored **1.0**. I closed it by also grading 2,000 fresh titles made from a random seed at every run; the lowest accuracy counts. That cheat now scores 0.1667.

---

## 2. Before-and-After Exam Table

- **Old exam:** 2,000 inputs (from my `tests/gen.py`)
- **New exam:** 100,000 inputs (`kit/make_pool.py` seed 1). Mode: `re` (WITHOUT regex). Answers frozen twice, 0 dropped (`kit/report.txt`).

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **my oracle (fixed)** | 0 | n/a | n/a | `measure/my-oracle.txt` |
| my oracle (before fix) | 7,380 | no (0 wrong of 2,000) | 0% | `measure/my-oracle-before-fix.txt` |
| **GunjitArora** | 4,948 | no (0 wrong of 2,000) | 0% | Follows the with-regex mode (0 wrong on the trainer's pool in that mode), so most of these are mode differences |
| **AlokKumarJaiswal** | 50,594 | yes (48 wrong of 2,000) | 0% | e.g. `d'arcy` → `D'arcy` (want `d'Arcy`) |

---

## 3. One Surprise

- **My own port was wrong on 7,380 of the 100,000 new titles**, yet it got all 2,000 old titles right.
- Breaking the 7,380 down by cause:

  | Cause | Wrong titles | Example |
  | :--- | :--- | :--- |
  | Leading underscore | 2,304 | `_dream` should stay `_dream`; my port gave `_Dream` |
  | `ß` | 1,123 | should become `SS` |
  | `ŉ` | 1,066 | should become `ʼN` |
  | `ﬁ` | 1,048 | should become `FI` |
  | The rest | 1,839 | mostly an upper-case small word at the end of a line (`… for AN` → `… for An`), plus `İ` → `i̇` and final `Σ` → `ς` |

- Why: in Python `re`, `CAPFIRST = ^[PUNCT]*?([\w])` is lazy, and `_` is both in PUNCT and in `\w`, so it stops at `_` and changes nothing. Python's `str.upper()` / `lower()` / `capitalize()` use full Unicode mappings. Go's `unicode.ToUpper` maps one character to one character.
- I fixed the port (still standard library only, no input removed). It now gets **0 wrong of 100,000**. It also gets 0 wrong on 704,000 more titles: the old exams, the trainer's pool, and 5 other seeds answered by Python 3.12.

---

## 4. Verification Proof Summary

All on the hardened task at commit `2702d02`, Harbor 0.25.0:

- **Oracle:** `1.0` (Job: `jobs/2026-11-19__17-47-31`) → `proof/oracle-reward.json`
  - Grader log: `100k=1.0000 old2k=1.0000 fresh=1.0000`
- **Nop:** `0.0` (Job: `jobs/2026-11-19__17-48-50`) → `proof/nop-reward.json`
- **Attacker cheats** → `proof/cheats-reward.txt`
  - Cheat 1: `0.1667` (Job: `jobs/2026-11-19__17-49-45`)
  - Cheat 2: `0.1667` (Job: `jobs/2026-11-19__17-50-58`)
  - Cheat 3: `0.1667` (Job: `jobs/2026-11-19__17-52-07`)
  - All attacker cheats score below `0.20`.

**Honest limits:**
- `build` still gives 1/6 = 0.1667 to any program that compiles. That is where the 0.1667 above comes from.
- The text check for hidden Python can be beaten by encoding the source (I tried it: base64 plus `syscall.Exec`). It still scored 0.1667, because the jail has no Python to run.
