# Attack on Sonu Kumar's titlecase-go task

Target: `SonuKumar/titlecase-go` at commit `a5918f4a0388388541231957cb18a423673e1b12` (see `TARGET.txt`).
Each cheat was run as `solution/solve.sh` in a scratch copy of the task. Nothing in the target's
`tests/`, `task.toml` or `environment/` was changed.
Runs: `harbor run -p sonu-cheatN -a oracle` (Harbor 0.25.0, Ubuntu WSL), one trial each, 0 exceptions.
The `jobs/` folders are not pushed. Each `verifier/reward.json` is copied into `results/`.

How the exam is scored: rewardkit turns every `.py` file in `tests/` into one group.
`reward.toml:4` weights them `behaviour = 4`, `build = 1`, `no_python = 1`. `criteria.py` is also
a group (weight 1, the default). Total weight = 7.

## Cheat 1 — Delete trick + echo program
What it does:   Deletes every `.py` file and writes a Go program that prints each input line
                unchanged. It contains no titlecase logic at all.
Score:          reward 0.7619  (build 1, no_python 1, behaviour group 0.667, criteria group 0.667;
                behaviour_check = 0.0, i.e. 0 % of outputs correct)
Job folder:     jobs/2026-11-19__08-09-08   (results/cheat1-reward.json)
Why it worked:  `tests/behaviour.py:6` imports `criteria`, so the `@criterion` functions
                `build_check` and `no_python_check` (`tests/criteria.py:23-37`) are counted inside
                the **behaviour** group too. 2 of its 3 criteria are free, and that group has weight 4
                (`tests/reward.toml:4`). So a program with 0 % correct outputs gets about 0.76.
How to fix:     Keep criteria in one module that the check files do not import. Make behaviour
                score only the output match, and give `build`/`no_python` points only if behaviour > 0.

## Cheat 2 — Read the exam at run time
What it does:   The Go program ignores its input. It opens `/tests/data/hidden_expected.txt`
                (falling back to `expected.txt`) and prints the file. No titlecasing.
Score:          reward 1.0  (build 1, no_python 1, behaviour group 1.0, criteria group 1.0)
Job folder:     jobs/2026-11-19__08-10-18   (results/cheat2-reward.json)
Why it worked:  The binary under test is run in the verifier container
                (`tests/criteria.py:60-66`), and that container holds the answers at the fixed
                paths in `tests/criteria.py:8-9` (copied in by `tests/Dockerfile:15`). The program
                can just read them.
How to fix:     Make the answers unreadable to the binary under test: run it as a different
                unprivileged user with `/tests` set to mode 700, or read the answers into memory
                and delete them before running it. Also run it with `cwd` set to a temp directory.

## Cheat 3 — Python inside a Go wrapper
What it does:   Base64-packs the original `titlecase/__init__.py` into `main.go` and deletes every
                `.py` file. At run time it writes the module to `/tmp` and runs it with the
                verifier's `python3` through `os/exec`. No Go port of the logic.
Score:          reward 1.0  (build 1, no_python 1, behaviour group 1.0, criteria group 1.0)
Job folder:     jobs/2026-11-19__08-11-29   (results/cheat3-reward.json)
Why it worked:  The verifier image is `python:3.12-slim` (`tests/Dockerfile:3`), so `python3` is on
                PATH while the binary runs. `instruction.md:20` bans `os/exec` and Python, but no
                check enforces it. `no_python_check` (`tests/criteria.py:34-36`) only looks at file
                suffixes, so Python hidden in a `.go` string passes.
How to fix:     Use a verifier image with no Python interpreter (or run the binary in a separate
                sandbox without one). Also reject sources that import `os/exec` or `syscall`
                (`go list -deps` / grep).

## Other weak points (not separate cheats)
- `task.toml:2` collects only `go.mod` and `main.go`. If Harbor gives the verifier only these,
  `no_python_check` can never see the `.py` files, so it may pass even when they were not deleted.
- `tests/criteria.py:76` gives partial credit per line. A half port that only capitalises words
  could get a large share of the behaviour score (not measured).

**Highest score any cheat got: 1.0 (Cheat 2 — Read the exam, and Cheat 3 — Python inside).**
