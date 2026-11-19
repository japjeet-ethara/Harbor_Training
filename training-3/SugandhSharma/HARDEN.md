# Hardening — SugandhSharma / titlecase-go

Task: `task/` (Go port of python-titlecase, graded by Reward Kit, weights build 1 / no_python 1 / behaviour 4,
reward = (build + no_python + 4 x behaviour) / 6). Bar for a cheat: below 0.2.

## The weakness

`no_python` paid 1 for any program that **built** and left **no `.py` file**, with no requirement that the
program actually port anything.

- File: `task/tests/no_python/check.py`, the old body ended `return go_build_passes(workspace)` — a build
  gate only, no behaviour gate.

So a program that writes a trivial `go.mod` + `main.go`, copies its input straight to its output, and deletes
the Python scored:

- build = 1 (it compiles)
- no_python = 1 (no `.py` left, build passes) — **free**
- behaviour = 0.045 (echoing the input is already correct for the ~4.5% of hidden titles that are in title
  case to begin with)
- reward = (1 + 1 + 4 x 0.045) / 6 = **0.3633** — above the 0.2 bar. A build-only non-port passed as a cheat.

The practice-1 README already listed this as the main thing to harden ("no_python paying only when the port
actually works").

## The fix

`no_python` now also requires the program to be right on **at least 25% of the hidden titles** — a real port,
not a build. Echoing the input clears only 4.5%, an empty program 0%; any genuine port clears far more (the
oracle 100%, and the broken ports in the mutation tests still 50%+), so the 25% line cleanly separates a port
from a non-port.

- File: `task/tests/no_python/check.py` — added `hidden_share_correct(workspace) >= REAL_PORT_MIN` (0.25),
  which builds the root program, runs it on `tests/data/hidden_inputs.txt` and compares with
  `hidden_expected.txt`.

The same build-only cheat now scores:

- build = 1, no_python = **0** (0.045 < 0.25), behaviour = 0.045
- reward = (1 + 0 + 4 x 0.045) / 6 = **0.1967** — below 0.2.

The worst-case calibration cheat `task/cheat/solve.sh` was also updated to this exact "build + delete `.py` +
echo input" program, so the shipped cheat demonstrates the closed hole.

## Proof (Harbor 0.25.0, reward files in `proof/`)

| Run | Before (build-only gate) | After (real-port gate) |
|---|---|---|
| oracle (real port) | 1.0 | **1.0** |
| nop (does nothing) | 0.0 | **0.0** |
| cheat: build + delete `.py` + echo input | **0.3633** | **0.1967** (below 0.2) |

- `proof/oracle-reward.json` → `{"behaviour":1.0,"build":1.0,"no_python":1.0,"reward":1.0}`
- `proof/nop-reward.json` → `{"behaviour":0.0,"build":0.0,"no_python":0.0,"reward":0.0}`
- `proof/cheat-before-reward.json` → `{"behaviour":0.045,"build":1.0,"no_python":1.0,"reward":0.3633}`
- `proof/cheat-after-reward.json` → `{"behaviour":0.045,"build":1.0,"no_python":0.0,"reward":0.1967}`

## Note on the margin

The cheat floor after hardening is 0.1967. It cannot go lower by changing `no_python` alone: a compiling
program always gets build = 1 (0.1667), and echoing the input always earns behaviour 0.045 (0.03) because 4.5%
of the hidden titles are already in title case — both fixed by the 1/1/4 weights and this hidden set. To widen
the margin, the hidden set could be regenerated to drop titles that are already correctly cased (identity near
0), which would take the echo cheat to 0.1667; that is a larger change (new hidden and visible data, re-verify
oracle and the mutation tests) and is not done here. The 25% gate already keeps every build-only cheat under
0.2, with the oracle at 1.0.
