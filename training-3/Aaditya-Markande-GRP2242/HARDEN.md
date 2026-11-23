# Day 5 Harden Report — Aaditya Markande

Attacker: Rudransh. His report is `rudransh-attack/attack/ATTACK.md`, which targets commit ee7e3df.

## Holes closed

| Cheat | Rudransh's score | My re-run on the old task | Now (hardened) |
|---|---:|---:|---:|
| 1 Visible answer lookup | 0.333 | 0.406 (job `2026-11-20__11-25-33`) | **0.079** (job `2026-11-20__11-13-55`) |
| 2 Read hidden answer file | 0.333 | **1.000** (job `2026-11-20__11-26-02`) | **0.000** (job `2026-11-20__11-14-26`) |
| 3 Relocate and call Python | 0.667 | 0.667 (job `2026-11-20__11-26-31`) | **0.000** (job `2026-11-20__11-14-55`) |

My numbers differ from Rudransh's for cheats 1 and 2. His runs used an isolated setup. In a real
`harbor run`, `tests/test.sh` ran the cheat's binary while `/tests` was mounted, so cheat 2 could read
`/tests/data/hidden_expected.txt` and print the answers: full marks 1.000. This was the worst hole.

Fixes (all in `task/tests/test.sh`):
- **Jail:** the port runs alone, as user 65534, with `chroot` into an empty folder that holds only
  the binary. It cannot see `/tests`, `/tmp`, `/workspace` or Python. This closes cheats 1, 2 and 3.
- **Gated score:** the reward is the behaviour score only. Build and no_python give no points
  by themselves, and a build that is not "clean" scores 0. (Before: `(build + no_python + 4*behaviour)/6`
  gave 0.333 for doing nothing.)
- **Clean check:** no `.py` file anywhere under `/workspace` (before: only `/workspace/repo`). No
  `os/exec`, `syscall`, `plugin`, `unsafe`, `import "C"`, `go:embed` or `go:linkname`. No `require`
  or `replace` in `go.mod`, and no `vendor` folder. Go source must stay under 400 KB, so a pasted
  answer table cannot hide in the code. Cheat 3 now gets `no_python` 0 because its wrapper imports `os/exec`.
- **Hidden data:** the old visible and hidden files are gone. Only `tests/data/inputs.txt` and
  `answers.txt` remain, and the jailed program cannot see them.

## Exam: before and after

Old exam: 2,000 hidden inputs. New exam: 100,000 inputs, mode: **regex** (stated in `instruction.md`).

- Pool: `kit/make_pool.py 100000 1` (seed 1).
- Answers: `kit/answers.py` on python-titlecase 2.4.1 inside the task's own image (Python with
  the `regex` module). It was run twice and kept 100000 of 100000, dropped 0 (`kit/report.txt`).

| Port | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|---|---:|---|---:|
| my oracle | 0 | n/a | n/a |
| NehaGaur | 488 | no (0 wrong of 2000) | 0% |
| AahanTrikha | 889 | no (0 wrong of 2000) | 0% |

Both ports would have scored 1.0 on my old exam. The new exam shows them. Files: `measure/`.

## What I learned
1. Do not trust an isolated run. The real harness decides what a cheat can read, and cheat 2 got 1.000 there.
2. Free points for build and no_python made any cheat score 0.333. Gate them behind real behaviour.
3. A 2,000-title exam missed ports that are wrong on 488 and 889 of 100,000 titles. What is in the inputs matters.
