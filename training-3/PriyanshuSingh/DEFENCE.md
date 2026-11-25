# DEFENCE — Priyanshu Singh, titlecase-go

Notes for the 5-minute talk. Every number has a job folder. All runs used Harbor 0.25.0,
Docker 29.9.2 and Windows 11 on 2026-11-20.

## The three proofs on my hardened task

These ran on `training-3/PriyanshuSingh/task` exactly as pushed (exported with `git archive`).

| Run | Must be | Got | Grader log | Job folder |
|---|---|---:|---|---|
| oracle | 1.0 | **1.0** | matched 101958 of 101958, printed 101958 | `jobs/proof-oracle/2026-11-20__17-34-03/task__rgFHbT5` |
| nop | 0.0 | **0.0** | `go: go.mod file not found` (build fails) | `jobs/proof-nop/2026-11-20__17-35-21/task__banZMsA` |
| Pragati cheat 1, echo | < 0.2 | **0.0** | 1505 of 101958 (1.48%) | `jobs/proof-pragati-cheat1/2026-11-20__17-36-06/pragati-cheat1__woystaW` |
| Pragati cheat 2, first letter | < 0.2 | **0.0** | 14485 of 101958 (14.21%) | `jobs/proof-pragati-cheat2/2026-11-20__17-37-15/pragati-cheat2__vaJsvBS` |
| Pragati cheat 3, echo + extra line | < 0.2 | **0.0** | 1505 of 101958, printed 101959 | `jobs/proof-pragati-cheat3/2026-11-20__17-38-22/pragati-cheat3__6ZudZea` |

The reward files are in `proof/`. Pragati re-attacked independently on Day 6 (her commit
`c2fa84e`). She got the same three 0.0 scores, plus 0.0 for a new cheat that searches the disk
for my answer files at run time.

Why I re-ran these: the "final" runs in `HARDEN.md` (11:32–11:38) came before my last task
commit (`46807dc`, 12:00). That commit changed only `README.md` and `cheat/solve.sh`, and
neither is graded. I re-ran everything on the pushed task anyway, so the proof matches what
the trainer will check out.

## 1. Strongest cheat: Pragati's cheat 2, first letter of every word

- **Before: 0.4693.** build 1 + no_python 1 + 4 × behaviour 0.204, divided by 6. The two checks
  that only test "it compiles" and "no .py file" paid 0.3333 for nothing.
- **After: 0.0.** It matches 14.21% of the new exam, which is under the 50% floor.
- Fixes, and where they live:
  - `tests/checks/build/build.py:20` and `tests/checks/no_python/no_python.py:23`: these checks now
    return the **behaviour score**, so they only pay when the program titlecases correctly.
  - `tests/lib/grading.py:28` and `:154-156`: behaviour is 0 at or below a 50% match share, then
    rises in a straight line to 1.0.
  - `tests/lib/grading.py:140`: the score divides by the **larger** of the expected line count
    and the printed line count. That closes cheat 3, where an extra line used to be ignored by
    `zip()`.

## 2. Exam: before and after

Old exam: 2,000 hidden titles. New exam: **101,958** titles (kit pool with 100,000 from seed 1,
plus the 1,958 old hidden titles not already in it). The mode is **re, titlecase WITHOUT
`regex`**, stated in `instruction.md`. The answers were frozen twice with 0 dropped
(`kit/report.txt`).

| Port | Wrong on new exam | Wrong on kit pool only | Old exam caught it? | Chance a random 2K exam misses it |
|---|---:|---:|---|---|
| my oracle | 0 | 0 | n/a | n/a |
| Ashish | 656 | 373 | yes (283 of 2,000) | 0% |
| Pragati Sharma | 238 | **0** | yes (238 of 2,000) | 1% |

Source: `measure/*.txt` (`kit/compare.py`).

## 3. One surprise

**The 100,000-title kit pool found zero bugs in Pragati's port. My 2,000 old titles found 238.**
Her bug is Unicode letters whose capital is longer than one letter (`ß` → `SS`, `ﬁ` → `FI`,
`ŉ` → `ʼN`). Python's `str.upper()` handles these and Go's `unicode.ToUpper` does not. The kit
pool never generates those letters, so if I had replaced my old exam instead of merging it in,
her port would look perfect. This is Lesson 1 from the guide, showing up the other way round:
what is in the exam matters more than how big it is.

## Honest notes (what did not go smoothly)

- I had not thought of Pragati's cheat 3 (print one extra line) myself, and my grader ignored it
  until her report.
- On Windows the kit scripts write `\r\n` line endings and fail to print Unicode to a pipe under
  `-I`. I generated the exam in `python:3.14-slim` (Linux) instead.
- Harbor crashes on a Windows console with a cp1252 encoding error from its progress spinner.
  Setting `PYTHONUTF8=1` fixes it. The crashed runs ran no trial, and I deleted them.

## Questions I expect

- *Why keep the old 2,000 titles?* They are the only titles with Unicode case expansion. Without
  them, Pragati's 238-title bug is invisible (see the surprise above).
- *Why a 50% floor, not 90%?* A real port that is close (for example, wrong only on Unicode case
  expansion) should still get some credit. Every cheat measured so far is at or below 19.7%, so
  50% leaves a wide gap between cheats and real ports.
- *Can the program read the answers?* No. It runs as `nobody` after `chmod -R go-rwx /tests`
  (`tests/test.sh:6`), in a separate verifier container (`task.toml:19`) whose image has no
  system Python (`tests/Dockerfile:12`). My own read-the-exam cheat and Pragati's new probe
  both scored 0.0.
- *Can a leftover process change the reward?* No. Every process owned by `nobody` is killed
  after each run (`tests/lib/grading.py` `kill_leftovers`) and once more before the reward is
  written (`tests/test.sh:24`). My linger cheat scored 0.0 (`jobs/final-self-linger/2026-11-20__11-54-19`).

## My re-attack on Ashish (Day 6, step 6.2)

My three Day 4 cheats on his hardened task (`abb5dbf`) went 1.0 / 1.0 / 0.4185 → **0.0 / 0.0 /
0.0**, with his oracle still at 1.0. Details are at the end of `attack/ATTACK.md`.
