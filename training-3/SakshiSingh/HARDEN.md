# HARDEN — Sakshi Singh's titlecase-go task (Day 5)

Attacker: Vansh Gupta (`training-3/VanshGupta/attack/ATTACK.md`).
All job folders are in my local `jobs/` folder (not pushed, as the guide says).

## Holes closed

Every "before" run is Vansh's cheat, unchanged, on my task before any change.
Every "after" run is the same cheat on the hardened `task/`.

| Cheat | Before (job) | After (job) | Fix |
|---|---|---|---|
| Vansh 1 — visible answer lookup | **0.3333** (`jobs/2026-11-20__11-25-52`) | **0.0** (`jobs/2026-11-20__11-59-07`) | `build` and `no_python` now only score if the port is real: behaviour ≥ 0.5 (`tests/port_check.py:36,148-149`, `tests/build.py:14`, `tests/no_python.py:14`). The free 2/6 is gone. The 100k exam also has no visible copy. |
| Vansh 2 — cgo probe | **0.0** (`jobs/2026-11-20__11-28-03`) | **0.0** (`jobs/2026-11-20__12-01-31`) | Already 0 (his C code did not build). Now cgo is off for every build (`CGO_ENABLED=0`, `tests/port_check.py:62`), so C cannot be used even if it compiles. |
| Vansh 3 — read `/tests/data/hidden_expected.txt` | **1.0** (`jobs/2026-11-20__11-30-24`) | **0.0** (`jobs/2026-11-20__12-03-21`) | The old grader ran the port as root next to `/tests`. Now the port runs in a chroot jail: an empty folder that holds only the static binary, as user `nobody` (65534) (`tests/port_check.py:102,125-126`). Inside it there is no `/tests`, no Python, no shell, no other program. |
| Extra: "Python inside" (my own Day 4 cheat 2: rename the Python library, embed it in Go, call `python3`) | not run before | **0.0** (`jobs/2026-11-20__12-04-29`) | Same jail: there is no `python3` to call. I checked this because Vansh may try a new cheat on Day 6. |

Proof on the hardened task:
- oracle **1.0** (`jobs/2026-11-20__11-55-22`), behaviour 1.0 on all 100,000 titles
- nop **0.0** (`jobs/2026-11-20__11-57-19`)

Note on re-running Vansh's cheats: his `solve.sh`, `main.go` and `go.mod` are committed with Windows
CRLF line endings, so bash fails on `set -euo pipefail\r` before the cheat even starts. I converted
only the line endings (the code is identical; checked with `diff`) so the cheats really ran.
My "before" scores match his report exactly: 0.3333 / 0.0 / 1.0.

## Exam: before and after

Old exam: 2,000 hidden inputs (pure ASCII — not one tab, non-breaking space or non-English letter).
New exam: 100,000 inputs from `kit/make_pool.py 100000 1`, answers frozen twice with `kit/answers.py`,
**mode: `re` (WITHOUT the `regex` package)** — 0 dropped (`kit/report.txt`). The mode is stated in `instruction.md`.
I added one word bank (`MINE`) to `make_pool.py`: ordinals, `Q&A`, `AT&T's`, contractions, brackets,
ellipses, curly quotes, all-caps apostrophes, small words glued to punctuation.

| Port            | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|-----------------|-------------------|---------------------|----------------------------|
| my oracle       | 0                 | n/a (0 wrong on old too) | n/a                   |
| Devansh Kakwani | 928               | no (0 wrong of 2,000) | 0%                       |
| Vansh Gupta     | 5                 | no (0 wrong of 2,000) | 90%                      |

Numbers are in `measure/my-oracle.txt`, `measure/devansh-kakwani.txt`, `measure/vansh-gupta.txt`.
Both classmates' ports read one title per line on stdin, so no wrapper was needed (I ran their
`solution/solve.sh` in a `golang:1.23` container to produce the Go code, then built and ran it).

- Devansh's port goes wrong on words that start with `_` (`_self-made` → `_Self-Made`, want `_self-Made`).
  The new pool has these; my old pool had none.
- Vansh's port goes wrong only on `v._` / `vs._` at the start of a title (5 titles). A 2,000-title
  exam would miss this 90% of the time — only the full 100,000 catches it.

## Problems I hit (honest list)

1. My first hardened grader put all three checks in one file `grade.py`. rewardkit scores each `.py`
   file as one input named after the file, so `reward.toml` could not find `build` / `no_python` /
   `behaviour`. Fixed: three small criterion files plus a shared `port_check.py` (no criterion of its own).
2. `chroot` lives in `/usr/sbin`, which is not on the verifier's `PATH`. Fixed: full path.
3. rewardkit runs the three criteria at the same time in threads. Without a lock, two threads built and
   deleted the jail at once and the oracle crashed. Fixed: one lock, each check runs once
   (`tests/port_check.py:41`), and a fresh `mkdtemp` jail per run.
   All runs made with the broken versions were deleted; none of them are used above.

## What I learned (3 lines)

1. A grader that runs the port as root, next to the answers, can be beaten by a 10-line program — where the binary runs matters as much as what it is checked against.
2. Weird inputs beat many inputs: my 2,000 pure-ASCII titles caught neither classmate's bug; the kit's strange words caught Devansh's 928 at once.
3. Size still matters for the last bugs: Vansh's 5 wrong titles slip past a 2,000-title exam 90% of the time.
