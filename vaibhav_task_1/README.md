# titlecase-go — Day 3 practice task (Harbor)

A complete Harbor task, built from the real open-source project
[python-titlecase](https://github.com/ppannuto/python-titlecase)
(MIT, SHA `42f43e2de55bf003b286c6f8e8d8b2d26676a167`): the agent must port the
library to Go so that it gives **byte-for-byte** the same output as the
original Python `titlecase()`, and delete the Python.

## Verify in one command (no Docker, no network)

```bash
bash verify/run_local.sh          # needs Go >= 1.23 and Python >= 3.11
```

Expected result (also saved in `results/`):

```
oracle       reward=1.0000   build=1  no_python=1  behaviour=1.0000
nop          reward=0.0000   build=0  no_python=0  behaviour=0.0000
cheat        reward=0.1667   build=1  no_python=0  behaviour=0.0000
RESULT: PASS
```

This replays each Harbor trial locally. It makes a fresh copy of the repo, as the
Docker image would, runs the agent, then runs the **real `tests/test.sh`** from a
separate copy of `tests/`. On Harbor, `test.sh` fetches the real Reward Kit
with `uvx`. Offline, `run_local.sh` points it at `verify/rewardkit_shim/`, a
tiny stand-in that implements the documented `@criterion` and
weighted-mean `reward.toml` behaviour. Use `USE_REAL_REWARDKIT=1 bash
verify/run_local.sh` to use the real package if you have network access.

More checks:

```bash
python3 verify/mutation_test.py   # 22 small wrong changes to the oracle — all must be caught
python3 verify/fuzz_vs_python.py  # oracle vs original Python on 70,000 extra lines — 0 diffs
```

## With real Harbor + Docker

```bash
bash verify/harbor_validate.sh    # docker build check, then oracle / nop / cheat runs
harbor view ./jobs                # screenshots of the three rewards for hand-in
```

`harbor_validate.sh` runs exactly the commands from the PDF:
`harbor run -p ./titlecase-go -a oracle`, `-a nop`, and the cheat check. For the
cheat check it backs up `solution/solve.sh`, copies `cheat/solve.sh` over it,
runs the oracle, then restores the real solution.

## Layout

```
NOTES.md                       Step 1: SHA, licence, 15 rules with checked examples,
                               and the examples I first got wrong
HANDIN.md                      Step 8: three rewards + the two lines
python-titlecase/              the original repo at the SHA (without .git), used by gen.py
titlecase-go/                  THE HARBOR TASK
├── instruction.md             Step 3: what the agent reads
├── task.toml                  timeouts, resources, network allowlists, separate verifier
├── environment/
│   ├── Dockerfile             Step 2: FROM golang:1.23, repo copied to /workspace/repo
│   └── python-titlecase/      build-context copy of the repo (no .git)
├── solution/solve.sh          Step 6: the oracle, a hand-written Go port (stdlib only)
├── cheat/solve.sh             Step 7: prints the visible answers, ports nothing
├── tests/
│   ├── test.sh                verifier entry point → /logs/verifier/reward.json
│   ├── gen.py                 Step 4: random.seed(1), 2000 visible + 2000 hidden titles
│   ├── data/                  inputs / expected / hidden_inputs / hidden_expected
│   └── checks/                Step 5: Reward Kit criteria
│       ├── build.py           weight 1: go build ./... passes
│       ├── no_python.py       weight 1: no .py left AND build passes
│       ├── behaviour.py       weight 4: share of HIDDEN lines matching exactly
│       └── reward.toml        weighted-mean 1 : 1 : 4
└── tools/
    ├── diff_first10.py        Step 6 helper: first 10 differing lines
    └── make_cheat.sh          regenerates cheat/solve.sh from expected.txt
verify/                        local runner, Reward Kit shim, mutation + fuzz tests,
                               real-Harbor script
results/                       reward.json / reward-details.json per run + logs
```

## Design decisions worth knowing

- **Which Python is the truth.** The module uses the `regex` package if it is
  installed and stdlib `re` otherwise, and the two branches behave
  differently. `gen.py` blocks `regex`, so the answers always come from the `re`
  branch. `instruction.md` names that branch, because otherwise the agent
  could not know which one is meant.
- **Hidden grading.** `behaviour` grades only `hidden_*.txt`, which the agent
  never sees (`environment_mode = "separate"`, and `tests/` is not in the image).
  Inside the verifier, the answer files are made root-only and the agent's
  binary runs as `nobody`, so a binary that looks for `/tests/data` at run time
  gets nothing (see the `read_hidden` baseline).
- **No free points.** `no_python` pays only if the build passes, so a
  do-nothing or delete-only agent scores 0.
- **Offline, pinned build.** Go is invoked with `GOTOOLCHAIN=local GOPROXY=off`.
  A `go.mod` that asks for a newer Go or a third-party module fails, as the
  instruction says.
- The agent's network is an empty allowlist. The verifier allowlist has only
  the hosts needed to install uv and Reward Kit.

## What was and wasn't run here

Everything in `verify/` was run, and the logs are in `results/`. Harbor and the
Docker daemon were not available in the environment this was built in, so
`verify/harbor_validate.sh` and the Docker build have **not** been run.
`test.sh`'s `uvx` path (the real Reward Kit 0.2.*) was not run either. Run
`harbor_validate.sh` on your machine to get the official screenshots.
