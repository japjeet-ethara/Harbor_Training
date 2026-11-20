# practice/titlecase-go

Harbor task: port the Python library [python-titlecase](https://github.com/ppannuto/python-titlecase)
(MIT, commit `42f43e2d…`) to Go with byte-for-byte identical output.

```
titlecase-go/
├── instruction.md            what the agent reads
├── task.toml                 timeouts, network, separate verifier, artifacts=/workspace/repo
├── NOTES.md                  repo SHA, licence, 14 rules + quirks (every example produced by the original)
├── environment/              golang:1.23 + a copy of the Python repo at /workspace/repo
├── solution/solve.sh         oracle: complete Go port (rune-level code, no look-around)
├── tests/
│   ├── test.sh               runs Reward Kit, writes /logs/verifier/reward.json
│   ├── Dockerfile            verifier image: Go + harbor-rewardkit 0.2.4 (no network needed)
│   ├── reward.toml           weighted-mean: build 1, no_python 1, behaviour 4
│   ├── build/check.py        go build compiles
│   ├── no_python/check.py    no .py file left AND build compiles
│   ├── behaviour/check.py    share of HIDDEN lines that match exactly
│   ├── gen.py                deterministic generator (seed 1); answers come only from the original code
│   └── data/                 inputs.txt, expected.txt (visible) + hidden_inputs.txt, hidden_expected.txt
├── cheat/solve.sh            cheat A: replays visible answers, leaves .py files      (needs < 0.2)
├── cheat/solve_deleting_py.sh cheat B: same, but also deletes .py files             (see HANDIN.md)
└── baselines/naive/solve.sh  hand-written naive port, a partial-credit reference (NOT an LLM run)
```

## Run it with Harbor (needs Docker)
```bash
harbor lint ./titlecase-go
harbor run -p ./titlecase-go -a oracle          # expect reward 1.0
harbor run -p ./titlecase-go -a nop             # expect reward 0.0
# cheat: back up, copy the cheat over the oracle, run, restore
cp titlecase-go/solution/solve.sh /tmp/solve.real.sh
cp titlecase-go/cheat/solve.sh titlecase-go/solution/solve.sh
harbor run -p ./titlecase-go -a oracle          # expect reward < 0.2
cp /tmp/solve.real.sh titlecase-go/solution/solve.sh
harbor view ./jobs
```

## Regenerate the data
```bash
pip install regex            # ground truth uses the `regex` branch (REGEX_AVAILABLE = True)
git clone https://github.com/ppannuto/python-titlecase ../python-titlecase && git -C ../python-titlecase checkout 42f43e2de55bf003b286c6f8e8d8b2d26676a167
python tests/gen.py          # or TITLECASE_REPO=/path/to/python-titlecase python tests/gen.py
```
