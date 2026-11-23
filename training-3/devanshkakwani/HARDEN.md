# Hardening my titlecase-go task (Day 5)

Author:   Devansh Kakwani
Task:     `training-3/devanshkakwani/task/`
Attacker: Sakshi Singh (`training-3/SakshiSingh/attack/ATTACK.md`, cheats `cheat{1,2,3}/solve.sh`)

Every score below is from a real `harbor run -p <task> -a oracle -o jobs` (or `-a nop`), run from
`training-3/devanshkakwani/`. For each cheat, `task/` was copied to `/tmp/hN` and only
`solution/solve.sh` was replaced with Sakshi's `cheatN/solve.sh`.

## Baseline (hardened task)

| Run | Reward | Job folder |
|---|---|---|
| oracle | **1.0** (build 1, source_check 1, behaviour 1) | `jobs/2026-11-23__07-05-55` |
| nop | **0.0** | `jobs/2026-11-23__07-06-53` |

Before hardening: oracle 1.0 (`jobs/2026-11-23__06-47-45`), nop 0.0 (`jobs/2026-11-23__06-49-01`).

## Holes closed

| Cheat | Before | After | Job before | Job after |
|---|---|---|---|---|
| 1 Lookup table + "capitalize every word" | 0.505 | **0.0** | `jobs/2026-11-23__06-43-58` | `jobs/2026-11-23__07-07-26` |
| 2 Python inside a Go wrapper | 0.9973 | **0.0** | `jobs/2026-11-23__06-45-04` | `jobs/2026-11-23__07-08-12` |
| 3 Download the exam over the network | 1.0 | **0.0** | `jobs/2026-11-23__06-46-05` | `jobs/2026-11-23__07-08-53` |

The "before" numbers match Sakshi's report exactly (0.505, 0.9973, 1.0).

### Cheat 1: lookup table (free points from build + no_python + partial credit)
- **Before -> after:** 0.505 -> 0.0 (`jobs/2026-11-23__07-07-26`: build 1, source_check 0, behaviour 0).
- **Fix:**
  - Gates instead of points: `tests/reward.toml:5` `aggregation = "all-pass"`. The reward is 1.0 only if build, source_check and behaviour all pass, else 0.0.
  - All-or-nothing behaviour on 100,000 + 2,000 lines: `tests/behaviour.py:38` (`EXAMS`) and `tests/behaviour.py:124` (any wrong line returns False).
  - The cheat's `//go:embed` table is rejected by `tests/source_check.py:46` (`BANNED_TEXT`) and `tests/source_check.py:127` (`EmbedPatterns`). Total Go source is capped at 256 KiB (`tests/source_check.py:36`).
  - `instruction.md:34` now says there is no partial credit.

### Cheat 2: Python inside (embedded `engine.txt` + `os/exec` of `/usr/local/bin/python3`)
- **Before -> after:** 0.9973 -> 0.0 (`jobs/2026-11-23__07-08-12`: build 1, source_check 0, behaviour 0)
- **Fix, in two independent layers:**
  1. **Python is unusable for the program.** `tests/Dockerfile:19` runs `chmod o-rwx` on python3.12, `libpython3.12.so.1.0`, `/usr/local/lib/python3.12`, perl, mawk, bash, dash and `/usr/local/go`. `tests/Dockerfile:30-31` runs `tests/lockdown_check.py` at build time: the image build fails unless `nobody` is denied all 8, and root Python is checked as a positive control.
     The binary runs as `nobody`, with no supplementary groups, `no_new_privs`, an empty environment, and `/tests`, `/logs/verifier` and the workspace set to `0700` (`tests/behaviour.py:53` `_lock_down`, `tests/behaviour.py:65-77` `_run`).
     The reason I do not use rewardkit's `Worker`: it starts a **Python** bootstrap (`_worker_bootstrap.py`) as the worker uid. That uid must be able to run Python, so the submission could too. Locally, cheat 2's binary prints the right answer as root and exits 1 as `nobody`.
  2. **A source check replaces the weak "no `*.py`" check.** `tests/source_check.py` (the deleted `tests/no_python.py`) rejects:
     - the imports `os/exec`, `syscall`, `plugin`, `unsafe`, `C` and `runtime/cgo`, plus `golang.org/x/sys` and `internal/` (`:40-41`);
     - `//go:embed`, `//go:linkname`, `//go:cgo_*`, `StartProcess`, `ProcAttr` and `#cgo` (`:46`);
     - `.py`, `.pyc` and `.so` files (`:39`);
     - any non-std, non-main-module package (`:116`);
     - any non-Go file over 64 KiB, ELF build output excepted (`:37`).

     Builds use `CGO_ENABLED=0 GOPROXY=off GOTOOLCHAIN=local` (`tests/build.py`).
- `instruction.md:14` states these rules, and `instruction.md:23` states the mode, which explains why cheat 2 lost 8 lines: in the verifier, Python ran in regex mode.

### Cheat 3: read the exam over the network
- **Before -> after:** 1.0 -> 0.0 (`jobs/2026-11-23__07-08-53`: build 0, source_check 0, behaviour 0; no Go was written)
- **Fix:** `task.toml:24` sets `network_mode = "no-network"` (in Harbor 0.25 the value is `no-network`; `"none"` fails validation and Harbor then treats the folder as a dataset). The cheat's `curl` to raw.githubusercontent.com fails, and `set -e` stops the solve.
  My oracle needs no network: it is pure Go standard library, and I built it with `docker run --network none golang:1.23 go build`.
  The old hidden files that Sakshi downloaded (`tests/data/hidden_*.txt`) are deleted, and the new 100k exam replaces them.

## Exam: before and after

- **Old:** 2,000 hidden inputs (`tests/data/hidden_inputs.txt`), partial credit per line.
- **New:** 100,000 inputs (`tests/data/inputs.txt` -> `tests/data/answers.txt`), mode: **re**, all-or-nothing. The old 2,000-line visible set is kept as an extra all-or-nothing regression set (`tests/data/regression_*.txt`).
- **Built with the kit** (`kit/`, the trainer's `06-kit.zip`), using `uv run --no-project --python 3.14 python -I`:
  - `make_pool.py 100000 1 pool.txt`
  - `answers.py task/environment/python-titlecase pool.txt key`
- **`kit/report.txt`:** pool 100000, kept 100000, dropped 0, regex module used False (re mode).

| Port | Wrong on new exam | Old exam caught it? | Chance a random 2K misses it |
|---|---|---|---|
| Mine, before the fix | 975 / 100,000 | **No** (0 wrong of 2,000) | 0% |
| Mine, after the fix (oracle) | 0 / 100,000 | n/a | n/a |
| Sakshi Singh | 0 / 100,000 | n/a (0 wrong of 2,000) | n/a |
| Abhishek Nain | 3,053 / 100,000 | Yes (8 wrong of 2,000) | 0% |

The measurements are in `measure/` (`my-oracle-before-fix.txt`, `my-oracle.txt`, `SakshiSingh.txt`, `AbhishekNain.txt`).
Each port was built in `golang:1.23` with `--network none` and run on `key/inputs.txt`, then scored with `compare.py key got.txt 2000`.
Both ports read one title per line from stdin, so no wrapper was needed. Abhishek's was run with an empty `HOME`, because it reads `~/.titlecase.txt` as a word list.

My port's four re-mode bugs, all fixed in `task/solution/solve.sh` (and the copy in `task/main.go`):
1. **Leading `_`.** CAPFIRST is `^[PUNCT]*?(\w)`, and `_` is `\w`, so `_self-made` keeps `_self`. Fixed in `capitalizeFirstAfterPunctuation` (`solve.sh:415`).
2. **`v.` before a small word.** SUBPHRASE's greedy `v\.?` swallows the dot, so `. v. the` leaves `the` lower. Fixed by trying the dotted candidate first (`solve.sh:493`).
3. **Non-ASCII capitals.** UC_ELSEWHERE and UC_INITIALS are ASCII-only, so `-ΑLPHA` becomes `-Αlpha` and `ÜBER/` becomes `Über/`. Fixed in `isUpperLetter` (`solve.sh:59`).
4. **APOS_SECOND.** `[\w]+` allows `_` and digits, so `D'Angelo_` becomes `d'Angelo_`. Fixed in `apostropheSecond` (`solve.sh:330`).

## What I learned
1. A small fixed exam only tests what its author thought of. My old 2,000 lines had no word starting with `_`, so it passed a port with 975 errors. 100,000 random lines exposed them at once.
2. Every point that doesn't need a correct port is a free point. Use gates (`all-pass`) and all-or-nothing scoring, and close the network, or a lookup table or a download beats the task.
3. "No Python" has to hold where the binary runs, not just in the file names. I also had to read the grader's own code: rewardkit's Worker needs Python for the same user it runs the binary as.
