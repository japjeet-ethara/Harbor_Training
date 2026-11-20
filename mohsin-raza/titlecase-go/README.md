# titlecase-go — Harbor task

Port `python-titlecase` 2.4.1 (`titlecase()`) to Go, byte-for-byte identical, with no Python left.

```
titlecase-go/
├── task.toml                 task + separate-verifier config, artifact = /workspace/repo
├── instruction.md            what the agent sees
├── NOTES.md                  repo, SHA, licence, the rules, rare cases
├── environment/
│   ├── Dockerfile            FROM golang:1.23, copies python-titlecase -> /workspace/repo
│   └── python-titlecase/     the original project (no .git)
├── tests/                    only exists in the verifier container
│   ├── Dockerfile            golang:1.23 + uv
│   ├── test.sh               runs Reward Kit -> /logs/verifier/reward.json
│   ├── checks/               build (1) · no_python (1) · behaviour (4), weighted mean
│   ├── gen.py                makes data/*.txt from the ORIGINAL Python (seed 1)
│   └── data/                 inputs.txt, expected.txt, hidden_inputs.txt, hidden_expected.txt
├── solution/solve.sh         oracle: Go port + deletes .py
└── cheat/solve.sh            prints the visible answer sheet; must score < 0.2
```

## Commands

```bash
# regenerate the data (deterministic; needs only python3)
python tests/gen.py                       # looks for ../python-titlecase or environment/python-titlecase

docker build -t titlecase-go-env environment/
harbor run -p ./titlecase-go -a oracle    # expect 1.0
harbor run -p ./titlecase-go -a nop       # expect 0.0

# cheat check
cp solution/solve.sh /tmp/solve.real.sh && cp cheat/solve.sh solution/solve.sh
harbor run -p ./titlecase-go -a oracle    # expect < 0.2
cp /tmp/solve.real.sh solution/solve.sh   # put the real oracle back
```

## Scores measured locally (verifier run through the real Reward Kit 0.2.4, no Docker)

| Scenario | build | no_python | behaviour | reward |
|---|---|---|---|---|
| oracle (`solution/solve.sh`) | 1 | 1 | 1.000 | **1.0** |
| nop (nothing done) | 0 | 0 | 0 | **0.0** |
| cheat (`cheat/solve.sh`) | 1 | 0 | 0.000 | **0.1667** |
| builds, echoes input unchanged | 1 | 0 | 0.049 | 0.199 |
| only deletes `.py` files | 0 | 0 | 0 | 0.0 |
| empty `go.mod` + deletes `.py` | 0 | 0 | 0 | 0.0 |

Note the cheat stays under 0.2 only because it leaves the `.py` files in place (build 1/6 ≈ 0.167).
A cheat that also deleted them would get 2/6 ≈ 0.33; this is a property of the 1/1/4 weights.
