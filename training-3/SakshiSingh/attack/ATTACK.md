# Attack on Devansh Kakwani's task

Target: `devanshkakwani/` at commit `fad90c9b6276db6a73cfd6d9feed4a8393e15547` (see `TARGET.txt`).
Every cheat is only a `solution/solve.sh`, run with `harbor run -p <scratch copy> -a oracle`.
No file in the target's `tests/`, `task.toml` or `environment/` was changed.

Baseline: the target's own oracle scored **1.0** (job `jobs/2026-11-18__18-27-03`), so the harness works.

## Reading the task (Step 4.1)

| Question | Answer | Where |
|---|---|---|
| What the agent sees | Only the Python titlecase repo, copied to `/workspace/repo`. No `tests/` folder. | `environment/Dockerfile:5` |
| What is checked | `build` (`go build ./...` passes), `no_python` (no `*.py` files + 2 tiny cases), `behaviour` (hidden 2,000 lines, partial credit per line) | `tests/build.py:10`, `tests/no_python.py:10,23-26`, `tests/behaviour.py:46-50` |
| How it is scored | weighted mean, build 1, no_python 1, behaviour 4 | `tests/reward.toml:4` |
| Which inputs | `tests/data/hidden_inputs.txt` / `hidden_expected.txt` (2,001 lines each) | `tests/behaviour.py:10-11` |
| Is `tests/` visible while the agent works | No. The verifier runs in a separate container, and the binary runs as a fresh user that cannot read `/tests`. | `task.toml:15`, rewardkit `Worker` |

The three weakest points:
1. **The network is open and the hidden answers are public.** `task.toml:24` has `network_mode = "public"`, and `tests/data/hidden_expected.txt` is committed to a public GitHub repo.
2. **`no_python` only checks file names.** `tests/no_python.py:10` looks for `*.py`. The verifier image is a Python image (`tests/Dockerfile:3`), and the binary is run inside it.
3. **A non-port gets free points.** `build` + `no_python` give 2/6 = 0.33 to any program that builds and passes two easy lines (`tests/no_python.py:23-26`), and many hidden lines are trivial (`i`, `j`, `k`...).

A strong point: the hidden inputs share **nothing** with the visible `tests/data/inputs.txt` (only the empty line is in both), so copying the visible answers does not help.

---

## Cheat 1 — Lookup table
What it does:   Go program with the visible `inputs.txt -> expected.txt` pairs built in; for any other line,
                it just capitalizes the first letter of every word. No titlecase rules at all.
Score:          reward 0.505  (build 1, no_python 1, behaviour 0.2575)
Job folder:     jobs/2026-11-18__18-27-48
Why it worked:  The lookup itself hit nothing (hidden inputs differ from visible ones — this part of the exam is strong).
                The points came from `tests/reward.toml:4` (build + no_python = 2/6 for any program that builds),
                `tests/no_python.py:23-26` (the two test lines are passed by "capitalize every word"),
                and `tests/behaviour.py:46-50` (per-line partial credit: the naive guess is right on 25.75% of hidden lines).
How to fix:     Give build / no_python points only if behaviour is also high (e.g. ≥ 0.9),
                and replace trivial hidden lines with hard ones where naive capitalizing is wrong.

## Cheat 2 — Python inside
What it does:   Copies the original `titlecase/__init__.py` to `engine.txt`, deletes all `*.py`, embeds it in a Go
                binary with `go:embed`, and at run time pipes stdin to `/usr/local/bin/python3` running that code.
Score:          reward 0.9973  (build 1, no_python 1, behaviour 0.996)
Job folder:     jobs/2026-11-18__18-30-00
Why it worked:  `tests/no_python.py:10` only checks for files named `*.py`; a renamed copy passes.
                `tests/Dockerfile:3` (`FROM python:3.12-slim-bookworm`) puts python3 in the same container where
                `tests/behaviour.py:28` runs the binary, so the binary can just call Python.
                The 8 lines it lost are not luck: `tests/Dockerfile:13` installs `harbor-rewardkit`, which pulls in
                `tiktoken` -> `regex`, so Python in the verifier runs titlecase in **regex** mode, while the answers
                come from **re** mode (checked locally: re mode 0 differences, regex mode 8, e.g. `listed on w3.ORG`).
                `instruction.md` never says which mode is meant.
How to fix:     Run the binary where there is no Python (separate minimal image, or remove/hide python3 before the
                Worker runs), and reject binaries that start other programs. State the mode in `instruction.md`.

## Cheat 3 — Read the exam (over the network)
What it does:   During the solve, `curl` downloads `hidden_inputs.txt` and `hidden_expected.txt` from the public
                GitHub repo (pinned to commit fad90c9), embeds them in a Go lookup table, guesses for anything else.
Score:          reward 1.0  (build 1, no_python 1, behaviour 1.0)
Job folder:     jobs/2026-11-18__18-31-10
Why it worked:  `task.toml:24` sets `network_mode = "public"`, so the agent can reach GitHub, and the hidden answers
                are in a public repo (`tests/data/hidden_expected.txt`). Reading `/tests` directly would fail —
                the attack goes around it.
How to fix:     Set `network_mode = "none"` in `task.toml` (a Go standard-library port needs no network).
                Also check that the Go source has no big embedded data files / tables.

---

**Highest score any cheat got: 1.0 (Cheat 3 — Read the exam over the network).**
