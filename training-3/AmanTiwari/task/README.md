# day3/titlecase-go

A Harbor task: port **python-titlecase** (v2.4.1, MIT,
commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`) to Go with byte-identical
output, then remove the Python code.

Mode: the reference answers come from titlecase **without the `regex` package**
(plain Python `re`, `REGEX_AVAILABLE = False`). Stated in `instruction.md`.

## Results (Harbor, local Docker)

Reward = **behaviour only**. build, no_python and no_exec are gates (weight 0):
behaviour is 0 unless all three pass. Hidden exam = **100,000** titles.

| Run | behaviour | build | no_python | no_exec | **reward** |
|---|---|---|---|---|---|
| Oracle | 1.0 | 1.0 | 1.0 | 1.0 | **1.0** |
| Nop | 0.0 | 0.0 | 0.0 | 0.0 | **0.0** |

Attacker (Ayush Singh) cheats, after hardening — were 0.333 / 0.438 / 1.0:

| Cheat | what it did | before | **after** |
|---|---|---|---|
| 1 build trick (empty program) | 0.333 | **0.0** |
| 2 half port | 0.438 | **0.14** |
| 3 Python inside (os/exec) | 1.0 | **0.0** |

## What changed on Day 5 (hardening)

See `../HARDEN.md`. In short:
- **Hard rules are gates, not points** (`tests/reward.toml`): reward = behaviour,
  and behaviour is 0 unless build + no_python + no_exec pass. Kills the build
  trick and caps the half port at its real match share.
- **New `no_exec` check** (`tests/no_exec/`): the program may not import
  `os/exec`, `syscall`, `unsafe`, `plugin` or `runtime/cgo`, may not contain a
  second `go.mod`, and may not use `StartProcess`/`go:linkname`. Kills "embed the
  Python source and run it with python3", including when `os/exec` is hidden in a
  replaced sub-module (checked with the author's own `go list ./...` imports).
- **Bigger, weirder exam**: 100,000 titles from `kit/make_pool.py` (seed 1),
  frozen twice by `kit/answers.py` (0 dropped), replacing the old 2,000.

## Layout

```
instruction.md          what the agent sees (now states the no-exec rule + mode)
task.toml               verifier: separate container, root-only /tests
environment/Dockerfile  golang:1.23 + the original repo at /workspace/repo
solution/solve.sh       oracle: writes go.mod + main.go, deletes all Python
cheat/solve.sh          legacy practice cheat (not used in the Day 6 proof)
tests/Dockerfile        verifier image: python 3.12 + golang 1.23, /tests root-only
tests/test.sh           uvx harbor-rewardkit -> /logs/verifier/reward.json
tests/reward.toml       reward = behaviour; build/no_python/no_exec are weight-0 gates
tests/_shared.py        build, no_python, no_exec and the gate helper
tests/{build,no_python,no_exec,behaviour}/  one check per folder
tests/data/             hidden_inputs/hidden_expected (100k, graded)
                        inputs/expected (first 2000, a human-readable sample)
```

## Anti-cheating

- Tests run in a **separate container**; the agent never sees `tests/` or `solution/`.
- Behaviour is graded on the **hidden** 100k set only; `tests/` is root-only and
  the program runs as unprivileged `runner`.
- **Gates, not points**: a program that builds but does nothing, or deletes the
  Python and nothing else, scores 0.
- **no_exec**: the program cannot shell out (e.g. to the image's python3) to let
  the original Python do the work.
