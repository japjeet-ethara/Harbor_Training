# HARDEN — Priyanshu Singh, titlecase-go

Attacker: **Pragati Sharma** (`training-3/PragatiSharma/attack/ATTACK.md`, pinned commit
`ef58d2a`, which is identical to my `task/` copy in commit `6727dd5`).

All runs: Harbor 0.25.0, Docker 29.9.2, Windows 11, 2026-11-20,
`harbor run -p <task copy> -a oracle -o jobs/<name>`. Each cheat ran in a copy of the task
with only `solution/solve.sh` replaced by Pragati's script.

## Holes closed

| Cheat (Pragati) | Her score | My re-run, old task | Job folder (old) | Final task | Job folder (final) |
|---|---|---|---|---|---|
| 1 Echo the input | 0.3823 | 0.3823 (b 1, np 1, beh 0.0735) | `jobs/pragati-before-cheat1/2026-11-20__11-10-25` | **0.0** | `jobs/final-pragati-cheat1/2026-11-20__11-35-06` |
| 2 First letter of every word | 0.4693 | 0.4693 (b 1, np 1, beh 0.204) | `jobs/pragati-before-cheat2/2026-11-20__11-11-55` | **0.0** | `jobs/final-pragati-cheat2/2026-11-20__11-36-49` |
| 3 Echo + one extra line | 0.3823 | 0.3823 (b 1, np 1, beh 0.0735) | `jobs/pragati-before-cheat3/2026-11-20__11-13-05` | **0.0** | `jobs/final-pragati-cheat3/2026-11-20__11-38-22` |
| oracle | | 1.0 | | **1.0** | `jobs/final-oracle/2026-11-20__11-32-22` |
| nop | | 0.0 | | **0.0** | `jobs/final-nop/2026-11-20__11-34-03` |

My re-runs gave the same numbers as Pragati's report.

Fixes:

1. **build and no_python paid for nothing (cheats 1, 2, 3).** On the old task, any program that
   compiled got 2 of 6 weight points (0.3333) from these two checks. Now
   `tests/checks/build/build.py` and `tests/checks/no_python/no_python.py` pay their condition
   **times** the behaviour score, so a program that titlecases nothing gets nothing from them.
2. **Partial credit for easy titles (cheats 1, 2).** Echo is right on titles that titlecase
   leaves unchanged; first-letter is right on simple titles. `tests/lib/grading.py` now gives
   behaviour 0 at or below a 50 % exact-match share, then a straight line up to 1.0 at 100 %.
   On the final exam echo matches 1.48 % and first-letter 14.21 %, both far under the floor.
3. **Extra output lines were never counted (cheat 3).** The old check used `zip()` and divided
   by the number of expected lines, so a line printed after the last title was ignored. Now
   `tests/lib/grading.py` divides the matches by the **larger** of the input count and the
   printed line count, and an unfinished last line (no `\n`) counts as a wrong line. The
   cheat 3 log shows it: `matched 1505 of 101958 hidden titles, printed 101959 lines`.
   `instruction.md` now says so.

What already held before Pragati's report (from my own earlier hardening): the program runs as
`nobody` after `chmod -R go-rwx /tests`, in a separate verifier image with no Python, and every
process it leaves behind is killed before the reward is written. Re-checked on the **final**
task with my own cheats (the three I used on Ashish, two self-tests, and my practice-1 cheat):

| Own cheat | Final task | Grader log | Job folder |
|---|---|---|---|
| Read the exam (look for answer files on disk) | **0.0** | 1.48 %: found nothing, echoed | `jobs/final-self-read-exam/2026-11-20__11-48-18` |
| Python inside (embedded original, run by `python3`) | **0.0** | program failed: no Python | `jobs/final-self-python-inside/2026-11-20__11-49-51` |
| Half port (easy rules only) | **0.0** | 19.68 %, under the 50 % floor | `jobs/final-self-half-port/2026-11-20__11-51-32` |
| Empty program that compiles | **0.0** | printed 0 lines | `jobs/final-self-empty/2026-11-20__11-53-01` |
| Linger (child process rewrites reward.json) | **0.0** | killed, real score kept | `jobs/final-self-linger/2026-11-20__11-54-19` |
| Practice-1 cheat (old visible answers) | **0.0** | printed 2,000 lines, 0 matched | `jobs/final-self-old-lookup/2026-11-20__11-55-50` |

## Exam: before and after

Old exam: 2,000 hidden inputs (from `tests/gen.py`).
New exam: **101,958 inputs, mode: re (titlecase WITHOUT `regex`)**.

How the new exam was made (`kit/`, the trainer's scripts, unchanged; run on Linux in
`python:3.14-slim` because on Windows the kit writes `\r\n` line ends and cannot print Unicode
to a pipe under `-I`):

1. `make_pool.py 100000 1 pool.txt`: 100,000 titles. The same seed gives the same file.
2. The old 2,000 hidden titles were added, without repeats (42 were already in the pool).
3. `answers.py` froze the answers twice: 101,958 kept, **0 dropped**, `regex module used False`
   (`kit/report.txt`). CPython 3.12 gives byte-identical answers.
4. `key/inputs.txt` and `key/answers.txt` went to `task/tests/data/`, replacing the old files.

Why the old titles stay in: the old exam has Unicode the kit pool never makes, where
upper-casing changes the length (`ŉ` → `ʼN`, `ﬁ` → `FI`, `ß` → `SS`). On the kit pool alone,
Pragati's port is wrong on **0** of 100,000 titles. On the old 2,000 it is wrong on 238.
Dropping them would have let that bug through.

Measured with `kit/compare.py` (outputs in `measure/`):

| Port | Wrong on new exam (101,958) | Wrong on kit pool only (100,000) | Old exam caught it? | Chance 2K random misses it |
|---|---|---|---|---|
| my oracle | 0 | 0 | n/a (0 wrong on old) | n/a |
| Ashish | 656 | 373 | yes (283 of 2,000 wrong) | 0% |
| Pragati Sharma | 238 | **0** | yes (238 of 2,000 wrong) | 1% |

The "kit pool only" column is what you get from the guide's commands as written
(`make_pool.py 100000 1`, then `answers.py`). It is in `measure/<port>-kit-only.txt`.
On that pool, Pragati's port looks perfect; only the old titles catch it.

Ports came from each person's practice-1 `solution/solve.sh`, built in `golang:1.23` with
`--network none`. All three read one title per line on stdin, so no wrapper was needed.

To re-run a number (the exam ships inside the task, so no pool has to be rebuilt):

```bash
cd ports/<port>    # the port's go.mod + *.go
docker run --rm -i --network none -v "$PWD":/w -w /w -e GOFLAGS=-mod=mod golang:1.23 \
  sh -c 'go build -o /tmp/port . && /tmp/port' < ../../task/tests/data/inputs.txt > got.txt
python -I ../../kit/compare.py ../../task/tests/data got.txt 2000
```

What the two ports get wrong (grouped by the first word that differs):

- **Both: letters whose capital is two letters.** Python's `upper()` turns `ß` into `SS`,
  `ﬁ` into `FI`, `ŉ` into `ʼN`. Go's `unicode.ToUpper` changes one letter into one letter, so
  `ß` stays `ß`. This also changes whether Python sees a line as ALL CAPS
  (`STRAßE`.upper() is `STRASSE`, which is not equal, so the line is not all caps).
  Pragati: almost all of her 238. My port has a special-casing table for this (`casing.go`).
- **Ashish: hyphen parts.** `X-RAY` in a normal line should be `X-Ray`: Python titlecases each
  part as its own line, so `RAY` on its own is all caps and gets lowercased first. His port
  keeps `RAY`. 219 of his 656, plus `T-SHIRT`, `pre-XML` and similar.
- **Ashish: `_` before a small word.** `_v` and `_an` at the start should be `_V` and `_An`.
- **Pragati: unusual separators.** A few lines with control characters such as `\x85` or
  `\x1c` between words come out different (e.g. `v.` printed as `V.`). Python's `\s` counts
  more characters as spaces than Go's `unicode.IsSpace`; I did not check each of these lines.

## What I learned (3 lines)

1. Re-running the attacker's cheats myself mattered: my own self-made cheats had not tried "print one extra line", and my grader still ignored it.
2. Weird inputs beat many inputs: 100,000 random kit titles found 0 bugs in Pragati's port, but my 2,000 old titles with `ŉ`, `ﬁ`, `ß` found 238.
3. A grader that pays points for "it compiles" turns every cheat into 0.33; every check has to be tied to correct output.
