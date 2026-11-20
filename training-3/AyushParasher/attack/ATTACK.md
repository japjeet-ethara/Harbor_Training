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

---

# Day 6 re-attack — Sonu's hardened task

Target: `training-3/SonuKumar/task` at commit `0b7d848` ("harden: close cheats 1-3, integrate 100k exam and
port comparisons"). Same method as before: each cheat is `solution/solve.sh` in a clean copy of that commit,
`harbor run -p <copy> -a oracle`, Harbor 0.25.0 (Ubuntu WSL), 1 trial, 0 exceptions. Weights are now
`build 0.5, no_python 0.5, behaviour 9` (`tests/reward.toml:4`).

Sanity check: his oracle scores **1.0** (`jobs/2026-11-20__08-33-33`).

| Cheat | Before (Day 4) | After (hardened) | Job folder | Per check (build / no_python / behaviour) |
|---|---|---|---|---|
| 1 Delete + echo | 0.7619 | **0.0623** | `jobs/2026-11-20__08-34-41` | 1 / 0 / 0.0137 |
| 2 Read the exam | 1.0 | **0.0623** | `jobs/2026-11-20__08-35-44` | 1 / 0 / 0.0137 |
| 3 Python inside | 1.0 | **0.05** | `jobs/2026-11-20__08-36-57` | 1 / 0 / 0 |
| 4 Half port (new) | — | **0.3936** | `jobs/2026-11-20__08-38-02` | 1 / 1 / 0.3263 |

Reward files: `results/reattack-cheat1..4-reward.json`.

## Cheats 1–3: closed
- **Cheat 2:** the binary now runs as `nobody` (`tests/criteria.py:129`), and `/tests` is root-only
  (`tests/Dockerfile:18`). The answer file cannot be opened, so the cheat falls back to echoing its input.
  That is why it scores the same as cheat 1: 1.37 % of titles are already in title case.
- **Cheat 3:** `/usr/local/bin/python*` is now mode 700 (`tests/Dockerfile:19`), so `nobody` cannot start
  Python, and `os/exec` is a banned import for `no_python` (`tests/criteria.py:22`).
- **Cheat 1:** `no_python` now needs a smoke test to pass (`tests/criteria.py:79`), so the echo program only
  gets the `build` points (0.05).

## Cheat 4 — Half port (new)
What it does:   A ~100-line Go program with only the easy rules: small words stay lowercase except in the first or
                last slot, other words get a capital first letter, inner capitals are kept, all-caps lines
                are lowercased first. It has no Mc names, apostrophes, slash/hyphen splitting, acronyms, initials,
                inline periods, subphrases or Unicode special cases. Not a real port.
Score:          reward 0.3936  (build 1, no_python 1, behaviour 0.3263)
Job folder:     jobs/2026-11-20__08-38-02   (results/reattack-cheat4-reward.json)
Why it worked:  Behaviour pays per line: `tests/criteria.py:146-147` returns `matching / total`, so getting a third
                of the titles right earns a third of the weight-9 behaviour score. The `no_python` gate is a
                single fixed title, "a tale of two cities" (`tests/criteria.py:79`), which any half port passes,
                and `build` (`tests/reward.toml:4`) is not gated at all.
How to fix:     Make behaviour (nearly) all-or-nothing, e.g. score 0 below 99 % correct, or use
                `(matching/total) ** k` with a large k. Gate `build` and `no_python` on that behaviour score
                instead of a one-line smoke test.

**Highest score after hardening: 0.3936 (Cheat 4 — Half port). It is above 0.2. Cheats 1–3 are all below 0.2.**
