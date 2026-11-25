# Day 5 Report — Hardening the Task

Task: `training-3/VanamPrashanth/task/titlecase-go`. Attacker: Mohammad Adnan (`training-3/MohammadAdnan/attack/ATTACK.md`).
All scores come from Harbor 0.25.0 runs (`harbor run -p <copy> -a oracle`, with the cheat as `solution/solve.sh`). Job folders are local and not pushed.

## Holes closed

### Cheat 1 — Read the exam
- **Before:** 1.0 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)
- **Job folder:** before `jobs/2026-11-18__14-54-11` (attacker), now `jobs/v3-adnan1`
- **Fix:** In `tests/checks/port_runner.py`, the grader reads the answers into memory first. It then runs the agent's binary alone in an empty `chroot` jail as user `nobody`, with no environment. Inside the jail there is no `/tests` and no answer file. `tests/Dockerfile` and `tests/test.sh` also run `chmod -R go-rwx /tests`.

### Cheat 2 — Python inside
- **Before:** 1.0 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)
- **Job folder:** before `jobs/2026-11-18__14-57-36` (attacker), now `jobs/v3-adnan2`
- **Fix:** The jail contains no `python3`, no shell and no other program, so the wrapper cannot start Python. `tests/checks/no_python.py` now also fails if any file contains Python source (`def titlecase(`, a Python shebang) or a Go file imports `os/exec`. It pays only if the port gets at least 80% of the hidden answers right.

### Cheat 3 — Lookup table + half port + delete trick
- **Before:** 0.728 (build 1.0, no_python 1.0, behaviour 0.592)
- **Now:** 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)
- **Job folder:** before `jobs/2026-11-18__15-00-01` (attacker), now `jobs/v3-adnan3`
- **Fix:**
  - The hidden inputs never appear in the visible file. `tests/gen.py` redraws overlaps; 73 had been shared.
  - `behaviour` scores 0 below 80% exact lines, then rises linearly to 1.0, so a half port earns nothing. Without the lookup it gets 56.95%.
  - `no_python` no longer pays for just deleting `.py` files.
  - Every run also adds 2,000 fresh titles from a random seed. The lowest accuracy counts, so copied or downloaded answers do not help.

The 0.1667 left is the `build` point (1 of 6): the cheats' Go code does compile.

**Proofs on the hardened task:** oracle **1.0** (`jobs/v3-oracle`), nop **0.0** (`jobs/v3-nop`).

---

## Exam: before and after

- **Old exam:** 2,000 inputs
- **New exam:** 100,000 inputs (`kit/make_pool.py` seed 1, answers frozen twice by `kit/answers.py`, 0 dropped), mode: `re` (WITHOUT regex). The old 2,000 and 2,000 fresh titles per run are graded too.

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
| :--- | :--- | :--- | :--- |
| **my oracle (fixed)** | 0 | n/a | n/a |
| my oracle (before fix) | 7,380 | no (0 wrong of 2,000) | 0% |
| **GunjitArora** | 4,948 | no (0 wrong of 2,000) | 0% |
| **AlokKumarJaiswal** | 50,594 | yes (48 wrong of 2,000) | 0% |

- GunjitArora's port follows the **with-regex** mode: it has 0 wrong on the trainer's pool in that mode. Most of its 4,948 are mode differences, not bugs.
- My port had real bugs that the new exam found: a leading `_`, Python's full Unicode case mapping (`ß`→`SS`, `İ`→`i̇`, final `Σ`), and the last small word (`AN`→`An`). I fixed the port. No input was removed.
- The kit scripts got two kinds of change:
  - **New word families** in `make_pool.py`, as Step 5.3 asks.
  - **Windows fixes**: UTF-8 output and LF line endings. These give byte-identical files to the original kit on Linux.

---

## What I learned

1. **Weird inputs beat many inputs.** My port passed all 2,000 old titles but was wrong on 7,380 of the new 100,000 (`_dream`, `ß`, `İzmir`).
2. **The grader must not trust the program.** Run as root next to the answers, a binary can read them or call Python. An empty jail closes both.
3. **Points must need real answers.** `no_python` and partial credit paid for no work. Now they need at least 80% correct, on titles nobody can know in advance.
