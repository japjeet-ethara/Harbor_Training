# HARDEN — Mohammad Adnan's `titlecase-go` (Day 5)

Attacker: **Charitra**. Their report is at `charitra/titlecase-go/Attack.md.md` on branch `training-3`
(commit `8caffa1`). It lists four weak points (reference code exposed at `/opt/python-titlecase/`,
build-only, delete-Python-only, partial port) but contains **no Harbor runs, no scores and no
`solve.sh` files** (all marked PENDING). So, as Step 5.1 asks, I wrote Charitra's three probes exactly
as described (`proof/cheats/c1`–`c3`) and ran them myself. I also turned Charitra's finding 1 into a
cheat (`c4`), and added the two cheats that beat Vanam's similar task (`c5`, `c6`).

"Before" = my practice-1 task as copied on Day 4 (commit `2f342fd`). "After" = `task/` now.
All job folders are under `jobs/` on my machine (not pushed); reward files are in `proof/`.

## Holes closed

| Cheat | Before | Job (before) | After | Job (after) | Fix |
|---|---|---|---|---|---|
| oracle (my port) | 1.0 | `jobs/2026-11-20__12-02-22` | **1.0** | `jobs/2026-11-20__12-48-21` | port fixed (see the exam section) |
| nop | 0.0 | `jobs/2026-11-20__12-05-02` | **0.0** | `jobs/2026-11-20__12-49-19` | — |
| c1 Charitra: build-only | 0.167 (build 1) | `jobs/2026-11-20__12-07-11` | **0.167** (build 1, accuracy 0) | `jobs/2026-11-20__12-50-08` | already below 0.2; `no_python` still 0 (the `.py` files stay) |
| c2 Charitra: delete-Python-only | 0.0 | `jobs/2026-11-20__12-09-42` | **0.0** | `jobs/2026-11-20__12-50-59` | already 0 (no Go program, no build) |
| c3 Charitra: partial port | **0.558** (build 1, no_python 1, behaviour 0.337) | `jobs/2026-11-20__12-11-58` | **0.167** (accuracy 0.167 → behaviour 0, no_python 0) | `jobs/2026-11-20__12-51-51` | 100,000 weird inputs + credit only above 50% |
| c4 copy the leaked port (Charitra finding 1) | **1.0** | `jobs/2026-11-20__12-14-28` | **0.0** | `jobs/2026-11-20__12-52-44` | reference port removed from the image |
| c5 read the exam | **1.0** | `jobs/2026-11-20__12-16-59` | **0.167** (accuracy 0.015) | `jobs/2026-11-20__12-53-36` | program runs as `nobody`, `/tests` locked |
| c6 Python inside | **1.0** | `jobs/2026-11-20__12-19-28` | **0.167** (Python found) | `jobs/2026-11-20__12-54-27` | no Python in either image + Python-source scan |

**Highest cheat score: before 1.0, after 0.167.** Reward files: `proof/before/`, `proof/after/`,
summary in `proof/cheats-reward.txt`.

**My first hardened version was not enough** (job folders `jobs/2026-11-20__12-43-33` and
`jobs/2026-11-20__12-45-33`): with locked answers and no Python, c3 still scored **0.445** (accuracy
0.167 earned behaviour 0.167 *and* unlocked `no_python`) and c5 scored **0.343**: reading `/tests` was
blocked, but its fallback simply echoes the input, and 1,502 of the 100,000 titles are already correct
as typed, which was enough for "at least one right answer". Fix 7 below closed both.

What I changed, file by file:

1. **Leak** — `environment/Dockerfile` copied `go-solution/` to `/opt/python-titlecase/` (old line 6),
   so any agent could copy my port (c4 = 1.0). The port now lives only in `solution/`, which Harbor
   uploads for oracle runs only (Day 6: written out by `solution/solve.sh` itself, see below).
2. **Python inside** — old agent image `golang:1.23` (Debian, has `python3`) and old verifier image
   `python:3.12-slim` let a Go wrapper run the original Python (c6 = 1.0). Both images are now
   `golang:1.23-alpine` pinned by digest, with no Python at all; the agent image adds `bash` and runs
   as user `player` (`task.toml` `[agent] user = "player"`). The grader also fails `no_python` and skips
   behaviour if Python code is found under any file name or inside the built binary
   (`tests/checks/no_python.go`: `def titlecase(`, `import regex`, `SMALL_FIRST = `, `Py_Initialize`).
3. **Read the exam** — the old `tests/behaviour.py` ran the program as root in the container that
   held `/tests/data/hidden_expected.txt` (c5 = 1.0). The new Go grader (`tests/checks/main.go`) first
   locks `/tests` and `/logs` to root (0700/0600), then runs the program as `nobody` (uid 65534) from an
   empty temp folder with a minimal environment (`tests/checks/behaviour.go`).
4. **Free `no_python`** — the old `tests/no_python.py` paid for "builds and no `.py`". Now
   `no_python` = build passed AND no Python found AND behaviour > 0 (`tests/checks/main.go`).
5. **Partial credit on easy inputs** — c3 scored behaviour 0.337 on the old 2,000 hidden titles,
   which were mostly plain lower-case words. Behaviour now uses the 100,000-title exam below.
6. **Two real bugs found on the way** — (a) my old `solve.sh` ran `go build ./...` after deleting the
   `.py` files; that fails with "build output titlecase already exists and is a directory" (the empty
   `titlecase/` folder). `solve.sh` now removes empty folders. (b) My first new grader had the same
   problem; it now builds `./...` with `-o` into a temp folder, so it never writes into the repo.

7. **Credit only for a port that really works** — `accuracy` = share of the 100,000 answers matched
   exactly; `behaviour = max(0, (accuracy − 0.5) / 0.5)`. An echo program (1.5%) and a port of only
   the easy rules (16.7%) get 0; a real port that is 96.5% right (like Vanam's) still gets 0.93. This
   rule is written in `instruction.md` ("How it is graded"), and `reward.json` also reports `accuracy`.

The grader is now Go (standard library only) instead of RewardKit, because the verifier image has no
Python. Weights are unchanged: `reward = (build + no_python + 4·behaviour) / 6`.

## Exam: before and after

Old exam: 2,000 hidden inputs. New exam: **100,000 inputs**, made with the trainer's kit
(`kit/make_pool.py 100000 1`, identical to `Downloads/06-kit`), plus one extra word family I added
(`EXTRA` in `kit/make_pool.py`: `1st`, `c++`, `AT&T`, `v._`, `_dream`, `Mcx-`, `d'arcy's`, …).
Answers frozen twice with `kit/answers.py` in `python:3.14-slim`: **100,000 kept, 0 dropped,
regex module used: False** (`kit/report.txt`). Mode stated in `instruction.md`:
**answers come from titlecase WITHOUT regex.**

| Port | Wrong on new exam (100,000) | Old exam caught it? (wrong on old 2,000) | Chance 2K random misses it |
|---|---|---|---|
| my oracle, before the fix | 1,627 | no (0 wrong) | 0% |
| my oracle, after the fix | **0** | n/a | n/a |
| Vanam Prashanth | 3,451 | no (0 wrong) | 0% |
| Charitra | 0 | n/a | n/a |

Files: `measure/my-oracle-original.txt`, `measure/my-oracle.txt`, `measure/vanam-prashanth.txt`,
`measure/charitra.txt` (each is the output of `kit/compare.py key got.txt 2000`).

**My own port was wrong on 1,627 of 100,000** and my old exam never saw it. It used the `regex`-mode
patterns (`\p{L}`), but the answers come from `re` mode, where `\w` also matches `_` and digits. So
`_dream` became `_Dream` instead of `_dream`. I fixed the port (`titlecase.go`, written by `solution/solve.sh`):
Unicode `\w` = `[\p{L}\p{N}_]` everywhere, the `re`-mode `UC_ELSEWHERE`/`UC_INITIALS` (ASCII),
Python-style `upper()` (`ß` → `SS`) for the all-caps test, `\x1c`–`\x1f` as spaces, rune count for the
consonant rule, and title-case in `capitalize()`. No input was removed. Vanam's port has related bugs
(`_a/b/c`, and a last small word after punctuation like `“machine ON` stays `ON`).

## What I learned

1. A cheat that scores low is only proof if it fails for the *right* reason — my first new grader
   rejected cheats because of a build-output clash that would also reject a correct port, and my
   first "fixed" `no_python` was still paid by a program that just echoes its input.
2. My 2,000-input exam passed three ports that are wrong on up to 3,451 of 100,000 titles: what is in
   the inputs (`_dream`, `“machine ON`) mattered far more than how many there were.
3. Stating the mode matters: my port silently mixed `regex`-mode and `re`-mode rules.
