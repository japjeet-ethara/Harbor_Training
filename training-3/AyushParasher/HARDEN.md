# HARDEN — Ayush Parasher, titlecase-go

Attacker: Saurabh Baghel (`training-3/SaurabhBaghel/attack/ATTACK.md`, attacked commit `53baf42`).
All runs: `harbor run -p <copy> -a oracle` (Harbor 0.25.0, Ubuntu WSL), 1 trial each, 0 exceptions.
Job folders are kept locally and not pushed.

## Holes closed

All three of Saurabh's cheats had the same root cause. The verifier ran the submitted binary **as root,
in the same container as the answers** (`tests/behaviour.py:6,17,20` in `53baf42`: `DATA` is `tests/data`, line 17 runs the binary as root,
and line 20 reads the answers from that same folder), so the binary
could open `/tests/data/hidden_expected.txt` at grading time. (His report says the answers were in the
agent's container. They were not: the agent image only copies `python-titlecase`. The leak was at
verification time.) A second hole: `build` and `no_python` paid 2/6 for no real work.

| Cheat (Saurabh) | Before (my re-run on `53baf42`) | After (hardened task) | Fix |
|---|---|---|---|
| 1 Direct hidden-answer read | 1.0 (`jobs/2026-11-20__05-22-23`) | **0.0** (`jobs/2026-11-20__05-19-10`) | answers unreadable to the binary |
| 2 Hidden input→answer map | 1.0 (`jobs/2026-11-20__05-23-11`) | **0.0** (`jobs/2026-11-20__05-20-00`) | same |
| 3 Recursive search (`/tests`, `/proc/1/root/tests`, `/solution`, `$HOME`) | 1.0 (`jobs/2026-11-20__05-24-00`) | **0.0** (`jobs/2026-11-20__05-20-48`) | same + `/proc/1/root` closed to `nobody` |
| Extra: Python inside a Go wrapper (my own cheat 3 vs Sonu) | not run | **0.0** (`jobs/2026-11-20__05-21-36`) | no system Python in verifier |

Saurabh reported 1.0 for all three (his jobs `2026-11-19__13-06-28`, `__13-09-08`, `__13-11-47`).

What changed (`git diff 9f106ae -- training-3/AyushParasher/task`):

1. `tests/test.sh`: `chmod -R go-rwx /tests` first, so only root can read the exam.
2. `tests/_grade.py` (new, no criteria of its own): reads inputs and answers into memory as root.
   Builds the port into a fresh temp dir. Runs it with
   `setpriv --reuid 65534 --regid 65534 --clear-groups --no-new-privs`, an empty env and cwd = that
   temp dir. As `nobody` the binary cannot read `/tests`, `/root` (where rewardkit's Python lives)
   or `/proc/1/root`.
3. `tests/Dockerfile`: deletes `/usr/bin/python3*` from the verifier image (the golang image ships
   Python 3.11), and the build fails if `python3` is still on PATH. This kills "Python inside".
4. `tests/build.py`, `tests/no_python.py`: each score is now `pass × behaviour score`. An empty or
   echo program that builds earns 0 instead of 0.33. `nop` stays 0.
5. `tests/data/`: removed the visible `inputs.txt`/`expected.txt` and the old hidden pair. There is now
   one exam, `inputs.txt` + `answers.txt` (100,000 lines), which lives only in `tests/`.
6. `solution/`: the real Go port. The practice-1 hand-in had the cheat committed there by mistake
   (fixed in `53baf42`, before the attack). Removed the old `cheat/` folder.
7. `instruction.md`: states the mode, and section 6 now describes the gated scoring and the
   unprivileged run.

## Exam: before and after

Old exam: 2,000 hidden inputs.   New exam: 100,000 inputs from `kit/make_pool.py 100000 1`, mode: **re**
(titlecase WITHOUT `regex`). `kit/answers.py` ran the original twice: kept 100,000, dropped 0
(`kit/report.txt`).

I added one word bank to `make_pool.py` (`EXTRA`: ordinals, `mp3`, `covid-19`, contractions, `'90s`,
`Mcx-`, `_dream`, `q&a`, `at&t`, `c++`, `.net`, `w/`, `n/a`, `...`, `À-la-carte`, `ß`, `ﬁne`).

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|------|-------------------|---------------------|----------------------------|
| my oracle | 0 | n/a (0 wrong of 2,000) | n/a |
| Sonu Kumar (`SonuKumar/titlecase-go`) | 4,963 | **no** (0 wrong of 2,000) | 0% |
| Saurabh Baghel (`training-3/SaurabhBaghel/task`) | 5,445 | **no** (0 wrong of 2,000) | 0% |

Numbers are from `kit/compare.py key got.txt 2000` → `measure/*.txt`. Each port was built from its
own `solution/solve.sh` in `golang:1.23`, then run with `--network none` on `key/inputs.txt`.
Sonu's `solve.sh` ends with `go build ./...`, which fails because of the emptied `titlecase/`
directory. His `go.mod` and `main.go` were already written, and they build and run fine.

Mode matters: on the regex-mode answers my port is wrong on 3,737 titles, Sonu's on 5,557 and
Saurabh's on 1,795. The two modes differ on 3,737 of the 100,000 titles. Saurabh's port is closer
to regex mode, but it is wrong on 1,795 titles even there.

Typical misses (both ports): `ß` → want `SS`; `_a/b/c` → want `_a/B/C`; `v1.2` and
`ıstanbul`-style Unicode; `ON` after `‘`.

## Proof on the hardened task (100k exam)

| Run | Reward | Job folder |
|---|---|---|
| oracle | **1.0** (build 1, no_python 1, behaviour 1) | `jobs/2026-11-20__05-17-42` |
| nop | **0.0** | `jobs/2026-11-20__05-18-32` |
| Saurabh cheats 1–3 + Python-inside | **0.0** each | see `proof/cheats-reward.txt` |

## What I learned
1. A port can score 1.0 on 2,000 hidden titles and still be wrong on about 5% of real input. What the exam contains matters more than its size.
2. The scariest hole was not the data: the grader ran untrusted code as root next to the answers. Run the code under test as a user who cannot read them.
3. "Free" checks (build, delete files) add up. Gate them on real behaviour, or nop-like cheats pass the 0.2 bar.
