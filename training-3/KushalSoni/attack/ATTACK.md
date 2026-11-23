# Attack report: Kushal Soni attacks Devansh Sharma

Target: `DevanshSharma/titlecase-go` at commit `9dc499b66a8a07b189b3449da772c6430ce087d0` (see `TARGET.txt`).
The copy at `training-3/DevanshSharma/task` (branch `training-3`, commit `58e8de8`) is byte-for-byte the same task (`git diff` shows no difference), so these results apply to it too.

## How the exam works (what I read first)

- The agent works in `environment/Dockerfile:1` (`FROM ubuntu:24.04`). There is no Go and no Python in that image, and `tests/` is not inside it.
- `task.toml:15` sets `environment_mode = "separate"`. Harbor copies `/workspace/repo` (`task.toml:2`) into a second container and grades it there.
- That grading container is `tests/Dockerfile:1` (`FROM python:3.12-slim`). It contains Python 3, and `tests/Dockerfile:13` copies all of `tests/` to `/tests/`, including the hidden answers.
- `tests/behaviour.py:40-46` runs the solution's own program **inside that same container**, as the same user, with no sandbox.
- Score = weighted mean (`tests/reward.toml:4`): build 0.25, no_python 0.25, behaviour 4.0. A program that builds but gets every answer wrong still scores 0.5 / 4.5 = 0.1111.
- `behaviour` gives partial credit, one point per matching line (`tests/behaviour.py:51-61`).

Hidden exam: 2,000 lines in `tests/data/hidden_inputs.txt`. Only 38 of them also appear in the visible `inputs.txt`, so a lookup table of visible answers would not help much (Devansh's own cheat already showed this: 0.1111).

## How I ran the cheats

For each cheat I took Devansh's task exactly as committed (`git -c core.autocrlf=false archive 9dc499b DevanshSharma/titlecase-go`), put the cheat in `solution/solve.sh` and ran `harbor run -p <copy> -a oracle`. I did not change `tests/`, `task.toml` or `environment/`. The reward files are in `results/`.

Note: my first three runs (`jobs/2026-11-23__11-23-46`, `__11-26-12`, `__11-27-47`) gave no score. Windows `core.autocrlf=true` had turned the scripts' line endings into CRLF, and the verifier failed with `/tests/test.sh: cannot execute: required file not found`. Exporting the committed files with `git archive` fixed this, and the runs below are the real ones.

---

## Cheat 1: Read the exam

What it does:   A Go program with no titlecase logic. It throws away stdin, opens
                `/tests/data/hidden_expected.txt` (or searches the disk for it) and prints it.
Score:          reward **1.0**  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-23__11-52-32
Why it worked:  `tests/behaviour.py:7-8` keeps the answers at `/tests/data/hidden_expected.txt`, and
                `tests/behaviour.py:40-46` runs the solution's binary in the same container with full read
                access to `/tests` (copied there by `tests/Dockerfile:13`). Hiding `tests/` from the
                agent is not enough. The agent's *program* can still read them at grading time.
How to fix:     Read the expected answers into memory first, then make `/tests` unreadable
                (`chmod -R 700 /tests`) and run the binary as an unprivileged user (e.g. `nobody`),
                or run it in a separate container that has no `/tests` at all.

## Cheat 2: Python inside

What it does:   The original Python `titlecase/__init__.py` is stored inside `main.go` as a base64
                string. The Go program decodes it and runs it with `python3 -c`. There is no `.py`
                file anywhere and no real Go port.
Score:          reward **1.0**  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-23__11-55-15
Why it worked:  `tests/no_python.py:42` only looks for files ending in `.py`, so Python hidden in a
                string passes. The grading image `tests/Dockerfile:1` is `python:3.12-slim`, so
                `python3` is on the PATH when `tests/behaviour.py:40-46` runs the binary.
How to fix:     Run the binary with an empty `PATH` and as a user that cannot run `/usr/local/bin/python3`,
                or in a Go-only container with no Python. Also make `no_python` fail if the program
                imports `os/exec` or `syscall` (check with `go list -f '{{.Imports}}' .`).

## Cheat 3: Half port

What it does:   About 40 lines of Go with only the two easiest rules: capitalise every word, and keep
                small words (a, an, the, of, ...) lowercase except first and last. No Mc, apostrophes,
                acronyms, domains or all-caps handling.
Score:          reward **0.4862**  (build 1, no_python 1, behaviour 0.422)
Job folder:     jobs/2026-11-23__11-57-56
Why it worked:  `tests/behaviour.py:51-61` gives one point per matching line, so a port that knows
                two rules still gets 42% of behaviour. 105 of the 2,000 hidden inputs are empty lines
                (any program that echoes an empty line gets them free), and many hidden titles are
                plain words that need no special rule.
How to fix:     Remove the empty lines from the hidden inputs, add many more inputs that hit the hard
                rules (Mc, d'/o', acronyms, all-caps lines, domains, odd spacing), and make behaviour
                stricter: for example 0 unless at least 99% of lines match.

---

**Highest score any cheat got: 1.0 (Cheat 1 and Cheat 2, with no real Go port at all).**
