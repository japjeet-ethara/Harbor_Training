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

## The fix (two parts, both needed)

1. **`no_python` now requires a real port** — right on **at least 25% of the hidden titles**, not just a build.
   File `task/tests/no_python/check.py`: added `hidden_share_correct(workspace) >= REAL_PORT_MIN` (0.25), which
   builds the root program, runs it on `tests/data/hidden_inputs.txt` and compares with `hidden_expected.txt`.
   Without this, a non-port still collected `no_python` for free.

2. **The hidden exam now contains only titles that need real work.** File `task/tests/gen.py`: the `take()`
   filter drops every title the original leaves unchanged (a fixed point of `titlecase`), so a program that
   just echoes its input is right on **0%** of the hidden titles instead of 4.5%. Both the visible and hidden
   sets were regenerated; `python tests/gen.py` still reproduces them deterministically.

Together, a program that builds, deletes the Python and echoes its input now fails the 25% gate (no_python 0)
and earns no behaviour, so it scores **(1 + 0 + 0) / 6 = 0.1667** — the floor a compiling program can reach,
below the 0.2 bar. The worst-case calibration cheat `task/cheat/solve.sh` is this exact program.

## Proof (Harbor 0.25.0, reward files in `proof/`)

| Run | Before (original task) | After (hardened) |
|---|---|---|
| oracle (real port) | 1.0 | **1.0** |
| nop (does nothing) | 0.0 | **0.0** |
| cheat: build + delete `.py` + echo input | **0.3633** | **0.1667** (below 0.2) |

- `proof/oracle-reward.json` → `{"behaviour":1.0,"build":1.0,"no_python":1.0,"reward":1.0}`
- `proof/nop-reward.json` → `{"behaviour":0.0,"build":0.0,"no_python":0.0,"reward":0.0}`
- `proof/cheat-before-reward.json` → `{"behaviour":0.045,"build":1.0,"no_python":1.0,"reward":0.3633}` (original task)
- `proof/cheat-after-reward.json` → `{"behaviour":0.0,"build":1.0,"no_python":0.0,"reward":0.1667}` (hardened)

## Robustness is preserved

Regenerating the hidden set did not weaken the exam. The mutation test (`dev/mutants.py`, 115 one-change broken
ports) still catches **114 of 115** on the new hidden set; the one it does not change any output at all (an
equivalent mutant). See `dev/mutation_report.txt`.

## Note on the floor

0.1667 is the lowest a cheat can reach: any program that compiles gets the build point (1/6 = 0.1667), fixed by
the 1/1/4 weights, and the hidden set now gives a non-port no behaviour credit at all. The oracle stays at 1.0.
