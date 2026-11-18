# trainee/titlecase-go — Day 3 practice task

Port **python-titlecase 2.4.1** (MIT, `42f43e2`) to Go, standard library only, with output that is **byte-for-byte identical** to the Python `titlecase()` on every line. The Python is removed; only the Go twin remains.

## Layout

```
titlecase-go/
├── instruction.md            # what the agent reads
├── task.toml                 # timeouts, non-root agent, no agent internet, separate verifier
├── NOTES.md                  # Step 1: repo, SHA, licence, 15 rules + surprising cases
├── environment/
│   ├── Dockerfile            # golang:1.23-bookworm + repo at /workspace/repo (no .git)
│   └── python-titlecase/     # copy of the original repo (build context)
├── solution/solve.sh         # oracle: writes go.mod + main.go (Go port), deletes all .py
├── cheat/solve.sh            # Step 7 cheat: embeds VISIBLE expected.txt, ports nothing
├── cheat/solve_smart.sh      # stronger cheat: same, but also deletes .py files
├── tests/
│   ├── Dockerfile            # verifier image: Go 1.23 + Reward Kit 0.2.4 pre-installed (offline grading)
│   ├── test.sh               # runs Reward Kit -> /logs/verifier/reward.json
│   ├── gen.py                # Step 4: seed 1, 2000 visible + 2000 hidden, answers from the ORIGINAL code
│   ├── data/                 # inputs.txt, expected.txt, hidden_inputs.txt, hidden_expected.txt
│   └── checks/
│       ├── reward.toml       # weighted-mean: build 1, no_python 1, behaviour 4
│       ├── build/            # `go build ./...` passes
│       ├── no_python/        # no .py anywhere AND build passes
│       └── behaviour/        # share of HIDDEN lines matching exactly
└── scripts/
    ├── simulate.sh           # runs a trial with the same scripts and paths, without Docker
    ├── fuzz.py               # 150k-line differential fuzz of a Go binary vs the original
    └── mutate.py             # plants 13 bugs in the oracle and checks the hidden set catches each
```

The original repo must sit next to this folder (`../python-titlecase`) only to re-run `tests/gen.py`.

## Run it (on your laptop, with Docker)

```bash
harbor run -p ./titlecase-go -a oracle            # expect reward 1.0
harbor run -p ./titlecase-go -a nop               # expect reward 0.0
cp titlecase-go/solution/solve.sh /tmp/solve.bak  # cheat check
cp titlecase-go/cheat/solve.sh titlecase-go/solution/solve.sh
harbor run -p ./titlecase-go -a oracle            # expect ~0.167
cp /tmp/solve.bak titlecase-go/solution/solve.sh  # put the real one back!
harbor view ./jobs
```

If your Docker cannot enforce `network_mode = "allowlist"` for the agent, Harbor will refuse to run the trial. In that case, set it to `"public"` for local runs only.

## Results

These were produced with `scripts/simulate.sh`. It runs the real `solve.sh`, `test.sh` and Reward Kit at the real in-container paths, with the verifier seeing only `/workspace/repo` and `/tests`. Docker Hub was not reachable from the build machine, so these are not `harbor run` screenshots.

| Run | build | no_python | behaviour | **reward** | Target |
|---|---|---|---|---|---|
| oracle | 1 | 1 | 1.000 (2000/2000) | **1.000** | 1.0 ✅ |
| nop | 0 | 0 | 0 | **0.000** | 0.0 ✅ |
| cheat (`cheat/solve.sh`) | 1 | 0 | 0 | **0.167** | < 0.2 ✅ |
| smart cheat (also deletes .py) | 1 | 1 | 0 | **0.333** | ⚠️ see below |
| echo program, .py kept ("build only") | 1 | 0 | 0.036 | **0.190** | ≈ 0.17 |

Other checks:
- `harbor lint --select ALL` is clean apart from `unpinned-image`. To fix that, pin the digest using the command in the Dockerfile comment.
- `tests/gen.py` is deterministic: two runs diff to zero. All four files have 2000 lines.
- The oracle's Go code matches the original on **450,000 extra fuzz lines** (3 seeds × 150k, random titles and random character soup).
- Mutation testing: **13/13 planted bugs are caught** by the hidden set.

## Step 8 hand-in notes

**Rules most likely to break a port.** My port passed on its first build, so this ranking comes from mutation testing, not from failed attempts. The biggest silent failures were:
- the all-caps line test
- `capitalize()` lower-casing the rest of the word
- Python's Unicode `\s`/`\w`/`\b`, which Go's ASCII classes get wrong on NBSP and `é`
- the `y`-is-a-vowel acronym rule

The subtlest were `’` vs `‘` in the punctuation set and the greedy `v\.?` alternation order. That last one changes only 1 line in 2000.

**To make it harder:**
1. Score `behaviour` with **all-pass** instead of share-of-lines. Today a port with one bug scores 0.99+.
2. Gate `build`/`no_python` on `behaviour ≥ 0.5`. The smart cheat above gets 0.33 just for deleting files and compiling a lookup table.
3. Add a second hidden set built only from the rare paths in NOTES.md, such as leading/trailing whitespace, `’tis`, `v.x`, `x a.a` and Mc-recursion.
