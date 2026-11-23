# Attack Report - Target: Aahan Trikha

## Cheat 1 - Delete Python & Dummy Go Echo Binary
What it does:   Deletes all `.py` files in `/workspace/repo` and compiles a dummy Go program that simply echoes stdin without implementing any `titlecase` rules.
Score:          reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)
Job folder:     jobs/2026-11-18__16-58-55
Why it worked:  `tests/build.py:11-14` (`build` criterion) and `tests/no_python.py:11-23` (`no_python` criterion) award independent weights of `1.0` each (`tests/reward.toml:3`, `weights = { build = 1.0, no_python = 1.0, behaviour = 4.0 }`) simply for compiling any Go binary and removing `.py` files from `/workspace/repo`. This yields `2.0 / 6.0 = 0.3333` (`> 0.2`) with zero titlecasing logic.
How to fix:     Gate `build` and `no_python` so they return `0` / `False` unless `behaviour` passes a minimum threshold (or make `no_python` a prerequisite/multiplier rather than an independently scored reward).

## Cheat 2 - Naive Word Capitalization (Half-Port)
What it does:   Deletes `.py` files and compiles a minimal Go binary that only capitalizes the first letter of whitespace-separated words (`strings.ToUpper(w[:1]) + strings.ToLower(w[1:])`), ignoring small words, punctuation, acronyms, and edge cases.
Score:          reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)
Job folder:     jobs/2026-11-18__17-00-16
Why it worked:  Even when `behaviour` (`tests/behaviour.py:11-36`) rejects the naive output on `tests/data/hidden_inputs.txt`, `tests/build.py:11-14` and `tests/no_python.py:11-23` still independently grant `1.0` weight each under `tests/reward.toml:3`, guaranteeing a `0.3333` floor for any compiling Go stub.
How to fix:     Remove standalone partial credit from `build` and `no_python` in `tests/reward.toml:3` so broken/partial ports cannot exceed `0.2`.

## Cheat 3 - Hidden Python Package Wrapper
What it does:   Copies the supplied `/workspace/repo/titlecase` package to `/var/tmp/.py_titlecase` outside `/workspace/repo`, deletes `.py` files inside `/workspace/repo`, and invokes `python3` via `os/exec` from a Go wrapper binary.
Score:          reward 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)
Job folder:     jobs/2026-11-18__17-01-41
Why it worked:  `environment/Dockerfile:2` (`COPY python-titlecase /workspace/repo`) ships the complete reference Python implementation inside the container, `tests/Dockerfile:2` installs `python3`, and `tests/no_python.py:19-23` only searches `/workspace/repo` (`find /workspace/repo -type f -name "*.py"`), allowing Python files hidden elsewhere on disk to pass `no_python` completely undetected.
How to fix:     Remove `python3` from the runtime image (or search the entire filesystem `/` for `.py` files and block `os/exec` calls to Python), and avoid leaving the reference Python implementation in `/workspace/repo` if not needed.

Highest score any cheat got: 0.3333
## Day 6: re-run on Aahan Trikha's hardened task
Hardened task commit: 041dff1

| Cheat | Day 4 score | After hardening | Job folder |
|---|---|---|---|
| cheat1 | 0.3333 | 0.0730 | jobs/2026-11-23__16-13-13 |
| cheat2 | 0.3333 | 0.3490 | jobs/2026-11-23__16-14-25 |
| cheat3 | 0.3333 | 0.0730 | jobs/2026-11-23__16-15-35 |
