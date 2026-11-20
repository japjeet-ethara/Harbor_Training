# Harbor Attack Report: Sakshi Singh titlecase-go

Target commit: `9cbff6f9ccc63aba92b81028a591991a3ad98224`

Target repository mismatch: `Harbor_Training_3` did not exist as a GitHub repository or local checkout. The only accessible matching class repository was `japjeet-ethara/Harbor_Training`, whose target path is `Sakshi Singh/titlecase-go`; it was cloned locally as `Harbor_Training_3` for this exercise.

## Target analysis

The agent receives `/workspace/repo`, containing the original Python package and a Go module location. The verifier is separate, as declared by `task.toml:28-29`, and receives tests baked into `/tests` by `tests/Dockerfile:3-14`.

- Hidden inputs and expected answers are fixed in `tests/data/hidden_inputs.txt` and `tests/data/hidden_expected.txt`.
- The visible and hidden splits are generated deterministically in `tests/gen.py:151-170`; the first 2000 lines become visible and the rest become hidden.
- The build criterion only runs `go build -o ... ./...` and checks the exit code in `tests/build.py:27-41`. It does not inspect whether the implementation is Go, Go standard-library-only, or complete.
- The no-Python criterion first runs the build, then searches for leftover `.py` files in `tests/no_python.py:27-40`. It does not preserve or inspect the original source outside that simple file check.
- Behaviour builds the binary, reads hidden expected answers from `/tests/data/hidden_expected.txt`, reads hidden inputs from `/tests/data/hidden_inputs.txt`, and compares `splitlines()` in `tests/behaviour.py:10-11` and `tests/behaviour.py:28-56`.
- Reward weighting is 1 for build, 1 for no-Python, and 4 for behaviour in `tests/reward.toml:1-3`.
- The instruction explicitly makes hidden tests and hard rules binding in `instruction.md:28-31` and `instruction.md:50-54`.

The three weakest points are:
1. The hidden answer files are readable inside the separate verifier image, while the behaviour criterion does not isolate or verify the produced binary's answer-generation logic (`tests/behaviour.py:10-11`, `tests/behaviour.py:38-56`).
2. The visible corpus and expected answers are shipped in the task and deterministically generated (`tests/gen.py:151-170`), allowing exact visible-line memorization.
3. Build and no-Python checks validate only build exit status and `.py` file absence (`tests/build.py:27-41`, `tests/no_python.py:27-40`); they do not prohibit cgo or verify the implementation uses the intended algorithm.

### Cheat 1 – Visible Lookup Table

- What it does: Installs a Go binary containing exact mappings for all 2000 visible input/output pairs. Unknown lines produce a blank output.
- Why this approach was selected: It directly tests whether visible examples can substitute for implementation and whether behaviour credit is isolated from hidden cases.
- Actual reward score: `0.3333`.
- Individual check scores:
  - `build`: `1.0`
  - `no_python`: `1.0`
  - `behaviour`: `0.0`
- Harbor job folder: `Vansh Gupta/attack/jobs/2026-11-18__17-48-03/titlecase-go__pu7ZkXd`
- Exact weakness exploited: Visible answers are available and the hidden behaviour score is independent of visible-line overlap. The frozen data split is defined in `tests/gen.py:151-170`; behaviour only executes the hidden corpus in `tests/behaviour.py:38-56`.
- Recommended fix: Remove answer files from agent-reachable and verifier-reachable task artifacts where possible, add provenance/behavioral anti-lookup tests, generate non-cached randomized inputs, and require implementation-level or source-level checks where appropriate.

### Cheat 2 – cgo/C Language-Restriction Bypass

- What it does: Replaces the solution with a cgo-backed C implementation that only applies a simplistic first-letter/word character transformation.
- Why this approach was selected: The hard-rule text says Go standard library only, but the build criterion only invokes Go and never rejects cgo or C source.
- Actual reward score: `0.0`.
- Individual check scores:
  - `build`: `0.0`
  - `no_python`: `0.0`
  - `behaviour`: `0.0`
- Harbor job folder: `Vansh Gupta/attack/jobs/2026-11-18__17-50-33/titlecase-go__HkMJQTG`
- Exact weakness exploited: `tests/build.py:27-41` invokes only `go build` and has no source-language or cgo inspection. The no-Python check likewise only deletes/checks `.py` files in `tests/no_python.py:27-40`. This attack did not build successfully, so it received no credit.
- Recommended fix: Run a source scan rejecting cgo directives/import `"C"` and disallowed modules/imports, require pure-Go builds with `CGO_ENABLED=0`, and validate `go list -deps` or an allowlist of imported packages.

### Cheat 3 – Hidden Expected-Answer Read

- What it does: Replaces the binary with a program that opens `/tests/data/hidden_expected.txt` and copies it byte-for-byte to stdout.
- Why this approach was selected: The verifier explicitly reads hidden expected answers from `/tests/data/hidden_expected.txt` and executes the produced binary in the same separate verifier environment, where `/tests` is baked into the image.
- Actual reward score: `1.0`.
- Individual check scores:
  - `build`: `1.0`
  - `no_python`: `1.0`
  - `behaviour`: `1.0`
- Harbor job folder: `Vansh Gupta/attack/jobs/2026-11-18__17-53-57/titlecase-go__2ShNND3`
- Exact weakness exploited: The hidden expected-answer path is exposed to the produced binary at `tests/behaviour.py:10-11`; the binary is built and run after the test environment has loaded `/tests` at `tests/behaviour.py:28-56`.
- Recommended fix: Do not mount the hidden test image or answer files into the solution-readable environment. Run the candidate binary in a container that has only hidden inputs, keep expected answers outside the workspace, and compare outputs inside an isolated process without exposing answer paths. Add source/binary checks that reject direct reads of `/tests`.

## Highest actual score

The highest actual reward achieved was **1.0**, from Cheat 3 (`Hidden Expected-Answer Read`).
