# default/titlecase-go

Port the `python-titlecase` Python library to Go, matching its output byte-for-byte.

## How it works

The verifier image (`tests/Dockerfile`) is based on `golang:1.23` and includes `python3`
and `uvx`. When a trial runs:

1. Harbor copies the agent's `/workspace/repo` into the verifier via the `artifacts`
   declaration in `task.toml`.
2. `test.sh` runs inside the verifier. If `tests/data/` doesn't exist yet, it generates
   the 4000 test lines deterministically using `gen_verifier.py` — which imports
   `titlecase` from `/workspace/repo` (the original Python source).
3. `rewardkit` discovers `grader.py` and runs the three weighted criteria, writing
   `/logs/verifier/reward.json`.

This design means expected outputs are always produced by the ground-truth Python library,
never hardcoded.

## Local development

### Build the environment Docker image

Harbor uses `environment/` as the Docker build context:

```bash
docker build -t titlecase-go-env ./environment
```

Verify the Python files are present inside the container:

```bash
docker run --rm titlecase-go-env ls /workspace/repo
```

### (Optional) Pre-generate test data locally

```bash
# From the titlecase-go/ directory:
python tests/gen.py
```

This writes the same 4 data files that `gen_verifier.py` would generate at runtime.
You can commit them to avoid the generation step during verifier runs.

### Run with Harbor

```bash
# Oracle (should score 1.0)
harbor run -p ./titlecase-go -a oracle

# No-op (should score 0.0)
harbor run -p ./titlecase-go -a nop

# Cheat check (should score < 0.2)
cp solution/solve.sh solution/solve.sh.bak
cp cheat/solve.sh solution/solve.sh
harbor run -p ./titlecase-go -a oracle
cp solution/solve.sh.bak solution/solve.sh
```

## Expected rewards

| Run     | build | no_python | behaviour | reward  |
|---------|-------|-----------|-----------|---------|
| nop     | 0     | 0         | 0.0       | 0.000   |
| build only | 1  | 0         | 0.0       | ≈0.167  |
| cheat   | 1     | 1         | <0.1      | <0.200  |
| oracle  | 1     | 1         | 1.0       | 1.000   |

Weights: build=1, no_python=1, behaviour=4. Formula: `(1×build + 1×no_python + 4×behaviour) / 6`.

## Task structure

```
titlecase-go/
├── task.toml           — task config: artifacts, verifier mode, network
├── instruction.md      — instructions shown to the agent
├── environment/
│   ├── Dockerfile      — FROM golang:1.23, copies python-titlecase into /workspace/repo
│   └── python-titlecase/   — copy of the Python source (inside build context)
├── tests/
│   ├── Dockerfile      — FROM golang:1.23 + python3 + uvx
│   ├── test.sh         — entrypoint: generates data then runs rewardkit
│   ├── grader.py       — RewardKit criteria (build, no_python, behaviour)
│   ├── gen_verifier.py — generates test data inside the verifier
│   └── gen.py          — same generator for local use
├── solution/
│   └── solve.sh        — oracle: Go port of python-titlecase
└── cheat/
    └── solve.sh        — cheat: prints visible expected.txt (proves hidden grading works)
```
