# local/titlecase-go: Harbor practice task

Port the Python project [python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT) to Go, byte for byte, then delete the Python.

```
titlecase-go/
├── instruction.md            what the agent reads
├── task.toml                 timeouts, resources, separate verifier, artifacts, network
├── NOTES.md                  repo SHA, licence, 16 rules with verified examples, hardness evidence
├── environment/
│   ├── Dockerfile            golang:1.23-bookworm + python3 + non-root user "agent"
│   └── python-titlecase/     the original repo at SHA 42f43e2d... (no .git)
├── solution/solve.sh         oracle: Go port (go.mod + main.go), then deletes every .py
├── cheat/solve.sh            NOT a solution: prints the visible answers (proves hidden grading works)
└── tests/
    ├── Dockerfile            verifier image: Go 1.23 + Reward Kit 0.2.4 (no network needed)
    ├── test.sh               runs Reward Kit, writes /logs/verifier/reward.json
    ├── reward.toml           weighted-mean: build 1, no_python 1, behaviour 4
    ├── build.py / no_python.py / behaviour.py     the three checks
    ├── _common.py            shared helpers (no criteria)
    ├── gen.py                seeded generator; answers come ONLY from the original Python
    └── data/                 inputs.txt + expected.txt (visible), hidden_inputs.txt + hidden_expected.txt
```

## Run it

```bash
harbor lint ./titlecase-go
harbor run -p ./titlecase-go -a oracle          # expect reward 1.0
harbor run -p ./titlecase-go -a nop             # expect reward 0.0
cp solution/solve.sh /tmp/real.sh && cp cheat/solve.sh solution/solve.sh   # then:
harbor run -p ./titlecase-go -a oracle          # expect below 0.2 (0.1667)
cp /tmp/real.sh solution/solve.sh               # put the real one back!
harbor run -p ./titlecase-go -a claude-code -m <provider/model> --dry-run   # then without --dry-run
harbor view ./jobs
```

Regenerate the data (must give identical files every time): `python3 tests/gen.py`

## Results of the local verification

| run | build | no_python | behaviour | reward |
|---|---|---|---|---|
| oracle | 1 | 1 | 1.000 | **1.0** |
| nop (nothing done) | 0 | 0 | 0 | **0.0** |
| cheat (prints visible answers, keeps .py) | 1 | 0 | 0 | **0.1667** |
| build only (empty `main`) | 1 | 0 | 0 | 0.1667 |
| only `go.mod`, everything else deleted | 0 | 0 | 0 | 0.0 |
| shells out to python3 via `os/exec` | 1 | 0 | 0 | 0.1667 |

Also: the Go port was fuzzed against the Python original on 550,000 random lines with 0 differences.

## Checks (what is tested and why)

- **build (1)**: `go build ./...` passes AND the repo root builds a program (so a bare `go.mod` earns nothing).
- **no_python (1)**: no `*.py` anywhere under `/workspace/repo`, build passes, `go.mod` has no `require`/`replace`, no `os/exec` or `plugin` import.
- **behaviour (4)**: build the root program, feed it `hidden_inputs.txt`, score = share of lines identical to `hidden_expected.txt`.

## Honest notes

- Docker is not available in the sandbox this was built in, so `harbor run` itself was not executed. The verifier was run locally with the same Go (1.23.9), Reward Kit (0.2.4) and paths (`/workspace/repo`, `/tests`, `/logs/verifier`) the containers use. Please run the commands above once on your machine.
- `harbor lint` has no errors except `unpinned-image` (base images are pinned by tag, not by SHA-256 digest; digests could not be looked up offline).
- Ground truth is the stdlib `re` path of the original. The instruction says so, and `tests/gen.py` blocks the `regex` package.
- A cheat that hard-codes the answers AND deletes the `.py` files would score 0.33 (build + no_python). That is the designed partial credit, not a bypass of the hidden set.
