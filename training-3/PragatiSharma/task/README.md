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

This is the first hardening round. It grades against the 2,000-input hidden set below.

The verifier reports three checks. `build` and `no_python` are required conditions. The reward is the `behaviour` score when both pass, and `0` otherwise.

| Check | Role | Score |
| --- | --- | --- |
| `build` | Required | `1` when `go build ./...` succeeds in `/workspace/repo`, otherwise `0` |
| `no_python` | Required | `1` when the build succeeds and no `.py` file remains under the repository, otherwise `0` |
| `behaviour` | Reward | Fraction of the 2,000 hidden titles whose output matches, from `0` to `1`; `0` when a required condition fails |

`reward = behaviour` when `build = 1` and `no_python = 1`; otherwise `reward = 0`. `build` and `no_python` still appear in `reward.json` for diagnosis but carry no weight.

### Datasets (round 1, 2,000 inputs)

As the SOP requires, the generated inputs and answers are committed in `tests/data/`:

| File | Records | SHA-256 |
| --- | --- | --- |
| `hidden_inputs.txt` | 2,000 | `017c6ffc7992c0df12185961d24d4ca6266432eebb406c18bcf25e941664e852` |
| `hidden_expected.txt` | 2,000 | `4dcc8d7b9f0a866fb209de6ba171be07dfe30030d595959315cf1118af1daf9a` |
| `inputs.txt` (practice) | 2,000 | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` |
| `expected.txt` (practice) | 2,000 | `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` |

No hidden input appears in the practice set. 92 hidden titles are already titlecased, so a program that echoes its input scores `0.046`. Because the answers are committed, a program can memorise them; `../HARDEN.md` lists this as a remaining limitation.

### How the submitted program is run

- The verifier runs in its own container with `network_mode = "no-network"` (`task.toml`). With Harbor 0.25.0 on local Docker, this blocked HTTPS from the program, but DNS lookups still succeeded. `../HARDEN.md` has the measurements.
- The grader runs as root. It builds the program as root, then runs it as the unprivileged UID 40000 with `PATH=/usr/bin:/bin`. The working directory is a temporary directory containing the built binary. Any process the program leaves running is killed.
- `/tests` and the Python interpreter are readable only by root. The verifier image fails to build if UID 40000 can run Python or read the hidden answers.
- `/logs/verifier` is closed to the submitted program.

## Results

Round 1, hardened grader, 2,000 hidden inputs, Harbor 0.25.0. Job paths are in `../HARDEN.md`.

| Run | build | no_python | behaviour | reward |
| --- | --- | --- | --- | --- |
| Oracle | 1 | 1 | 1.0 | 1.0 |
| Nop | 0 | 0 | 0.0 | 0.0 |
| Cheat | 1 | 0 | 0.0 | 0.0 |

The cheat program ignores stdin and prints the 2,000 memorized practice answers from `tests/data/expected.txt` in their existing order. It deliberately leaves the original Python files in place. That passes the build check but fails the `no_python` condition, so the reward is `0`. Deleting the Python files would pass the condition, but the reward would then be only its behaviour score.

Pending: the 100,000-input exam and the three-port comparison.

`solution/solve.sh` is the reference port again. It matches `solution/solve.sh.backup-2427968cd9e644e2a82ebc000aa9ad2e` byte for byte. SHA-256: `91c5db4ce06cd206dff6dfb7485759520ff4b4c8e0fda5d14b8b3088b8ddb89e`.

## Screenshots (pre-hardening)

These captures show the original grader, before the Day 5 changes, when `reward = (build + no_python + 4 × behaviour) / 6`. They have not been retaken for the hardened grader, under which the cheat scores `0.0`.

![Pre-hardening: oracle reward 1.0](screenshots/oracle-reward.png)

![Pre-hardening: nop reward 0.0](screenshots/nop-reward.png)

![Pre-hardening: cheat reward 0.1667](screenshots/cheat-reward.png)

## Observations

1. The implementation report highlights apostrophe tails and case-sensitive subphrase handling as requiring manual string processing. No record of repeated implementation failures was preserved.

2. A harder variant could expand hidden Unicode cases targeting differences between Python and Go character classification and case conversion, while retaining the same stated behavior.
