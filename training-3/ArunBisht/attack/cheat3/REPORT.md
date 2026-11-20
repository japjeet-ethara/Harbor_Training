# Cheat 3 Audit and Validation

Date: 2026-11-18

## Original design and root cause

The original `solve.sh` tried to locate `tests/gen.py` and the Python snapshot using paths relative to its own location. Those files are not included in the agent image: the environment image copies only `environment/python-titlecase` into `/workspace/repo` (`../scratch-cheat3/environment/Dockerfile:13-17`). The generator and snapshot therefore were not available at the searched runtime paths. The script's fallback wrote a program that echoed stdin, so it could build and remove Python files but did not implement titlecasing. The task notes record unchanged-input output as a very low behavior baseline (`../scratch-cheat3/NOTES.md`, “Baselines”).

The generator branch was also inappropriate: it regenerated and copied `hidden_inputs.txt` and `hidden_expected.txt`, then embedded a lookup in the Go binary. This would replay the fixed evaluation set instead of implementing the requested behavior. It has been removed. No hidden input or answer file was opened, extracted, copied, embedded, or used during this repair.

No prior Cheat 3 result folder or collected artifact existed under `attack/results/jobs-cheat3`, so there is no previous actual Cheat 3 reward to report. The low behavior cause above is established from the old script's fallback and the task's documented baseline, not from an unavailable result JSON.

## Generator and test boundaries

- `../scratch-cheat3/tests/gen.py:15, 27-43, 194-214` seeds Python's `random` with `1`, verifies the pinned titlecase source digest, requires `regex` mode, shuffles generated titles, and writes 2,000 visible and 2,000 hidden input/answer rows as UTF-8 with LF newlines.
- The seed makes generation repeatable for a matching Python/runtime and dependency stack. The generator pins the original titlecase source, but does not pin Python or the `regex` package version; those are installed by apt in `../scratch-cheat3/environment/Dockerfile:4-8`.
- The public `inputs.txt` and `expected.txt` each have 2,000 aligned UTF-8 records, LF-only; there are no empty inputs or duplicate inputs. 1,148 rows contain non-ASCII characters, and 65 inputs end in a space.
- The verifier is separate (`../scratch-cheat3/task.toml:22-28`). Its Dockerfile copies tests under `/tests` and removes group/other access (`../scratch-cheat3/tests/Dockerfile:21-27`). The behavior runner executes the candidate as `nobody` and compares its output bytes to hidden expected rows (`../scratch-cheat3/tests/checks/behaviour/behaviour.py:26-66`).

## Changes made

- Replaced the hidden-data reconstruction and echo fallback in `solve.sh` with an installer that copies the local Go module/source into `/workspace/repo`, removes the Python package and `.py` files, then runs `go vet` and `go build`.
- Added a standalone Go 1.23 implementation in `port/main.go`. It processes stdin line by line, preserves whitespace, and implements the titlecase small-word, punctuation, phrase-start, compound-word, acronym, name, and Unicode rules using only the standard library.
- Updated the scratch task's `solution/solve.sh` and `solution/port/` with the same installer and implementation. The original task under `attack/target/` and its verifier were not changed.

Implementation entry points: `port/main.go:26-48` (Unicode case conversion), `port/main.go:110-174` (small words, initials and name rules), `port/main.go:230-281` (edge and subphrase handling), `port/main.go:284-361` (line/token transformation), and `port/main.go:363-382` (streaming interface).

## Tests and commands

- Public dataset: **2,000 passed, 0 failed (100.0000%)**, with 2,000 output rows.
- Additional Python-reference edge cases: **20 passed, 0 failed**, including empty and whitespace-only lines, Unicode, punctuation, compounds, and trailing spaces.
- `go vet ./...` and `go build -o /tmp/titlecase .` passed in a `golang:1.23` container with `GOTOOLCHAIN=local`, `GOPROXY=off`, and `CGO_ENABLED=0`.
- The host did not have Go installed; validation used Docker's pinned Go image.

Public-data validation command (Python drove the container and compared stdout byte-for-byte with the public expected file):

```powershell
@'
from pathlib import Path
import subprocess

root = Path(r"C:\Users\ArunBisht\Desktop\Arun")
source = root / "attack" / "cheat3" / "port"
data = root / "attack" / "scratch-cheat3" / "tests" / "data"
inputs = (data / "inputs.txt").read_bytes()
expected = (data / "expected.txt").read_bytes().splitlines()
cmd = [
    "docker", "run", "--rm", "-i", "-v", f"{source.as_posix()}:/src:ro",
    "golang:1.23", "bash", "-c",
    "cd /src && GOTOOLCHAIN=local GOPROXY=off GOFLAGS=-mod=mod "
    "CGO_ENABLED=0 go vet ./... && go build -o /tmp/titlecase . && exec /tmp/titlecase",
]
run = subprocess.run(cmd, input=inputs, capture_output=True)
assert run.returncode == 0, run.stderr.decode("utf-8", "replace")
actual = run.stdout.splitlines()
assert actual == expected, f"{sum(a != b for a, b in zip(actual, expected))} mismatches"
print(f"{len(expected)} passed, 0 failed")
'@ | python -
```

Harbor validation command:

```powershell
harbor run -p .\attack\scratch-cheat3 -a oracle --job-name attack-cheat3-repaired-20261118-2124 --jobs-dir .\attack\results\jobs-cheat3
```

## Harbor result and artifact evidence

- Job: `attack-cheat3-repaired-20261118-2124`
- Result directory: `../results/jobs-cheat3/attack-cheat3-repaired-20261118-2124/`
- Trial: `scratch-cheat3__esS5Uk9`
- Behavior: **1.000**
- Build: **1.000**
- No_Python: **1.000**
- Overall reward: **1.000**

Evidence: `../results/jobs-cheat3/attack-cheat3-repaired-20261118-2124/scratch-cheat3__esS5Uk9/verifier/reward.json` and `reward-details.json`. The collected program is `../results/jobs-cheat3/attack-cheat3-repaired-20261118-2124/scratch-cheat3__esS5Uk9/artifacts/workspace/repo/main.go`. Its SHA-256 is `4C6F5A8DBDEC54DD4D7495CDB4443477988850A64458158E00405221DD4610EF`, identical to `attack/cheat3/port/main.go`, confirming the intended implementation was collected. The collected `go.mod` declares module `titlecase` and Go `1.23`.

Harbor printed `fatal: bad revision 'HEAD'` and LiteLLM model-cost-map network warnings, but the job completed with zero errored trials and reward JSON containing 1.000 for every component.

## Remaining limitations

The current public suite and this Harbor evaluation have no observed mismatches. Unicode casing uses Go's Unicode tables plus explicit multi-rune uppercase mappings; Python has different Unicode/version-specific casing behavior for rare characters (for example, context-sensitive final Greek sigma). Such cases were not observed in the public comparisons or this Harbor score.
