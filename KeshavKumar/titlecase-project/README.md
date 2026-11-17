# titlecase-go: a Harbor task

A [Harbor](https://harborframework.com) task that asks an AI agent to **port
[python-titlecase](https://github.com/ppannuto/python-titlecase) (MIT, commit `42f43e2`) to Go**.
The Go program must reproduce the original `titlecase()` output byte for byte.

## Results

| Run | Behaviour | Build | No_Python | **Reward** | Target |
|-----|-----------|-------|-----------|------------|--------|
| oracle (`solution/solve.sh`) | 1.000 | 1.000 | 1.000 | **1.000** | 1.0 |
| nop (agent does nothing) | 0.000 | 0.000 | 0.000 | **0.000** | 0.0 |
| cheat (`cheat/solve.sh`) | 0.000 | 1.000 | 0.000 | **0.167** | < 0.2 |

Screenshots are in [`screenshots/`](screenshots/) (Harbor viewer) and `screenshots/terminal/`.

## Layout

```
titlecase-project/
├── python-titlecase/        original repo (separate git clone) + NOTES.md (rules + tricky cases)
├── titlecase-go/            the Harbor task
│   ├── instruction.md       what the agent is told
│   ├── task.toml            separate verifier; agent repo passed as artifact /workspace/repo
│   ├── environment/         Dockerfile (golang:1.23) + repo/ (copy of python-titlecase, no .git/NOTES.md)
│   ├── solution/solve.sh    oracle: Go port (standard library only), deletes all .py files
│   ├── cheat/solve.sh       cheat: prints the visible answers, ports nothing
│   └── tests/               verifier: Dockerfile, test.sh, Reward Kit checks, gen.py, data/
├── tools/compare_visible.py runs solve.sh in the task image, prints the first lines that differ
├── screenshots/
└── jobs/                    Harbor run results
```

## Grading (Reward Kit, weighted mean)

| Check | Weight | Scores 1 when |
|-------|--------|---------------|
| build | 1 | `go.mod` has no `require` (stdlib only) and `go build ./...` passes |
| no_python | 1 | no `.py` files, the build passes, **and** ≥ 50% of hidden lines are correct |
| behaviour | 4 | share of the 2000 **hidden** lines that match exactly (0 to 1) |

`reward = (build + no_python + 4 × behaviour) / 6`, written to `/logs/verifier/reward.json`.

Anti-cheat design:
- Grading uses only `hidden_inputs.txt`, which never overlaps the visible set.
- Every test title is one that `titlecase()` actually changes, so echoing the input scores 0.
- no_python is gated on real behaviour, so "trivial program + delete .py" earns nothing.
- Every cheat tried (visible answers, echo, with or without deleting `.py`) scores ≤ 0.167.

## How to run

Run from `titlecase-project/`, in PowerShell. Docker must be running.

```powershell
$env:PYTHONUTF8 = "1"        # Windows only: Harbor otherwise misreads UTF-8 files
harbor lint titlecase-go
harbor run -p ./titlecase-go -a oracle --job-name oracle
harbor run -p ./titlecase-go -a nop    --job-name nop
harbor view jobs                       # browse results
```

To run the cheat, back up `solution/solve.sh`, copy `cheat/solve.sh` over it, run the oracle
command, then **restore the real file**.

Regenerate the test data (deterministic, `random.seed(1)`; needs `python-titlecase/` next to
`titlecase-go/`):

```powershell
python titlecase-go/tests/gen.py
```

## Important details

- **Truth = the original Python**, run with the stdlib `re` fallback (`gen.py` blocks the
  optional `regex` module, which behaves differently). Expected answers are never hand-written.
  Python 3.11 (task image) and 3.13 produce identical answers for all 4000 lines.
- **The tests are hidden from the agent:** they are baked into the separate verifier image
  (`tests/Dockerfile`) and never copied into the agent's container.
- **The oracle port** re-implements every Python regex as plain character checks (Go's `regexp`
  has no look-around, and its `\w \s \b` are ASCII-only). It uses tables generated from Python
  3.13 vs Go 1.23 for full Unicode case mapping. Verified on 2000 visible, 2000 hidden and 20,000
  random fuzz lines.
- Keep PNGs and other binary files **out of** `titlecase-go/`: `harbor lint` reads every file
  as text.

## What makes the task hard

Python-vs-Go behaviour differences:
- Full Unicode case mapping: `ß`→`SS`, `İ`→`i̇`; this also changes the "all caps line" test.
- Python's Unicode-aware `\w`, `\s` and `\b` versus Go's ASCII-only versions.
- `IGNORECASE` quirks: `ı` matches `i`, and `ſ` matches `s`.

Quirky rules:
- The sub-phrase rule is case-sensitive and has no word boundary.
- `_` counts as both punctuation and a word character.
- `Mc` names are titlecased recursively (`mcdonald-smith` → `McDonald-Smith`).
- `DR SMITH` → `DR Smith`.

To make the task harder:
- Add inputs heavy in Greek, Turkish and German.
- Require the `callback`/wordlist and `preserve_blank_lines` options.
- Remove Python from the agent image so the original can't be run.
