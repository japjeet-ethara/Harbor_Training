# Day 5 Report — Hardening the Task

## Holes closed

### Cheat 1 — Read the exam
- **Before:** 1.0 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.0000 (build 0.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-19__16-35-02`
- **Fix:** In `tests/Dockerfile`, created an unprivileged `runner` user and restricted `/tests` permissions (`chmod 700 /tests`). In `tests/checks/behaviour.py`, the reference answers (`answers.txt`) are read into memory and unlinked from disk before the agent binary is executed as user `runner` in `/tmp`. The answer file does not exist on disk while the binary runs.

### Cheat 2 — Python inside
- **Before:** 1.0 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.1667 (build 1.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-19__16-37-52`
- **Fix:** In `tests/checks/no_python.py`, added deep file inspection checking for embedded Python source, `titlecase` signatures, `os.environ["TC_SRC"]`, and Python interpreter references. In `tests/Dockerfile`, restricted permissions on system Python (`chmod 700 /usr/bin/python*`).

### Cheat 3 — Build trick (Empty program)
- **Before:** 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)
- **Now:** 0.0000 (build 0.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-19__16-40-24`
- **Fix:** In `tests/checks/build.py` and `tests/checks/no_python.py`, added a smoke execution verification test (`the lord of the rings` -> `The Lord of the Rings`). An empty `main.go` fails the smoke test and scores 0.0 on `build` and `no_python`.

---

## Exam: before and after

- **Old exam:** 2,000 inputs
- **New exam:** 100,000 inputs, mode: `re` (WITHOUT regex)

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
| :--- | :--- | :--- | :--- |
| **my oracle** | 0 | n/a | n/a |
| **NehaGaur** | 9,935 | no (passed old exam) | 0.00% |
| **MadhurJain** | 3,232 | no (passed old exam) | 0.00% |

---

## What I learned

1. **Edge cases matter more than volume**: Words starting with leading underscores (`_dream`) or dotted versions (`v1.2`) expose subtle regex and tokenization bugs that thousands of clean titles never trigger.
2. **Exams must run in a secure sandbox**: Tests running as root or leaving answer files accessible on disk allow clever binaries to bypass solving entirely.
3. **Partial credit must be earned**: Allowing `build` or `no_python` to reward a submission without validating actual behavior allows empty programs to claim substantial credit.
