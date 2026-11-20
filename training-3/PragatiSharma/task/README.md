# ethara/titlecase-go

This Harbor task gives an agent a checkout of python-titlecase and asks it to replace that project with a Go command-line program. The program reads one title per line from standard input and writes the titlecased line. Its output must match the original `titlecase()` function called with default arguments, using this checkout's standard-library `re` branch. The program must use only the Go standard library, leave no `.py` files under `/workspace/repo`, and pass `go build ./...` from `/workspace/repo`.

## Prerequisites

- Docker, so Harbor can build the agent image (`golang:1.23`) and the separate verifier image.
- Harbor 0.25.0 on `PATH` (`harbor --version`).
- Run the commands below from this task directory.

Oracle runs `solution/solve.sh`. Nop leaves the Python repository unchanged.

## Commands

```bash
harbor run -p . -a oracle
harbor run -p . -a nop
```

Harbor writes each job under `jobs/`. That directory is local output and is not part of the submission.

## Scoring

This is the second hardening round. It grades against the 100,000-input exam below.

The verifier reports three checks. `build` and `no_python` are required conditions. The reward is the `behaviour` score when both pass, and `0` otherwise.

| Check | Role | Score |
| --- | --- | --- |
| `build` | Required | `1` when `go build ./...` succeeds in `/workspace/repo`, otherwise `0` |
| `no_python` | Required | `1` when the build succeeds and no `.py` file remains under the repository, otherwise `0` |
| `behaviour` | Reward | Fraction of the 100,000 exam titles whose output matches, from `0` to `1`; `0` when a required condition fails or the exam files do not hold 100,000 inputs and 100,000 answers |

`reward = behaviour` when `build = 1` and `no_python = 1`; otherwise `reward = 0`. `build` and `no_python` still appear in `reward.json` for diagnosis but carry no weight.

### Datasets (round 2, 100,000 inputs)

As the SOP requires, the generated inputs and answers are committed in `tests/data/`:

| File | Records | SHA-256 | Role |
| --- | --- | --- | --- |
| `inputs.txt` | 100,000 | `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` | Graded exam inputs |
| `answers.txt` | 100,000 | `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` | Graded exam answers |
| `practice_inputs.txt` | 2,000 | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` | Visible practice, not graded |
| `practice_expected.txt` | 2,000 | `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` | Visible practice, not graded |

- **Graded exam:** `../kit/make_pool.py` generated it (count 100,000, seed 1) and `../kit/answers.py` froze it from the original in standard-library `re` mode, with 100,000 kept and 0 dropped. `../kit/NOTES.md` has the commands, checks and word families.
- **Practice pair:** this is the round-1 practice set, renamed together and otherwise unchanged. `tests/gen.py` now writes only this pair and never writes `inputs.txt` or `answers.txt`.
- **Round-1 exam:** the 2,000-title round-1 hidden exam (`hidden_inputs.txt`, `hidden_expected.txt`) is no longer graded. It is kept unchanged in `../kit/evidence/old-exam-2000/` for the comparison report (`../measure/README.md`).
- **Echo floor:** 2,045 exam answers equal their input, so a program that echoes its input scores `0.02045`.
- **Overlap with practice:** one exam title (`dr`) is also a practice title.
- **Memorisation:** because the answers are committed, a program can memorise them; `../HARDEN.md` lists this as a remaining limitation.

### How the submitted program is run

- The verifier runs in its own container with `network_mode = "no-network"` (`task.toml`). With Harbor 0.25.0 on local Docker, this blocked HTTPS from the program, but DNS lookups still succeeded. `../HARDEN.md` has the measurements.
- The grader runs as root. It builds the program as root, then runs it as the unprivileged UID 40000 with `PATH=/usr/bin:/bin`. The working directory is a temporary directory containing the built binary. Any process the program leaves running is killed.
- `/tests` and the Python interpreter are readable only by root. The verifier image fails to build if UID 40000 can run Python or read the graded answers (`tests/data/answers.txt`).
- `/logs/verifier` is closed to the submitted program.

## Results

Round 2, hardened grader, 100,000-input exam, Harbor 0.25.0. Job paths, and the results for the three attack scripts, are in `../HARDEN.md`.

| Run | build | no_python | behaviour | reward |
| --- | --- | --- | --- | --- |
| Oracle | 1 | 1 | 1.0 (100,000 / 100,000) | 1.0 |
| Nop | 0 | 0 | 0.0 | 0.0 |
| Cheat | 1 | 0 | 0.0 | 0.0 |

The cheat program ignores stdin and prints the 2,000 memorized practice answers from `tests/data/practice_expected.txt` in their existing order. It deliberately leaves the original Python files in place. That passes the build check but fails the `no_python` condition, so the reward is `0`. Deleting the Python files would pass the condition, but the reward would then be only its behaviour score. On this exam that would be close to `0`, because its 2,000 fixed lines are not paired with the 100,000 exam inputs (not measured).

`solution/solve.sh` is the corrected reference port, SHA-256 `8546e114cf5e717f09f07d94c64ed31123edfb343fcc6d18316fc768fa69c0e8`.
- **Round 1 failures:** the round-1 port (`91c5db4ce06cd206dff6dfb7485759520ff4b4c8e0fda5d14b8b3088b8ddb89e`) failed 3,063 exam titles because Go's `strings.ToUpper` and `strings.ToLower` map one character to one.
- **What the corrected port does:** it reproduces Python's full case mappings, `\w`, `\s` and `re.IGNORECASE` folding, from tables generated with Python 3.14.2. It still uses only the Go standard library.
- **Tooling:** the generators and the 74 regression titles are in `../measure/oracle/tools/` and `../measure/oracle/regression/`.

Pending: new screenshots for the hardened grader.

## Screenshots (pre-hardening)

These captures show the original grader, before the Day 5 changes, when `reward = (build + no_python + 4 × behaviour) / 6`. They have not been retaken for the hardened grader, under which the cheat scores `0.0`.

![Pre-hardening: oracle reward 1.0](screenshots/oracle-reward.png)

![Pre-hardening: nop reward 0.0](screenshots/nop-reward.png)

![Pre-hardening: cheat reward 0.1667](screenshots/cheat-reward.png)

## Observations

1. The implementation report highlights apostrophe tails and case-sensitive subphrase handling as requiring manual string processing. No record of repeated implementation failures was preserved.

2. Round 2 did this. The 100,000-input exam adds Unicode word families: ligatures, dotted capital I, typographic apostrophes, symbols, emoji and other spaces. The original reference port failed 3,063 exam titles, all with ligatures or a dotted capital I. The corrected port reproduces Python's full case mappings, `re` character classes and `re.IGNORECASE` folding from tables generated with the reference interpreter. Its regression titles also cover dotless i, long s, U+001C to U+001F and Unicode 16 letters. `../measure/README.md` has the details.
