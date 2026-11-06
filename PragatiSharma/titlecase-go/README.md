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

The verifier reports three scores and a weighted mean:

| Check | Weight | Score |
| --- | --- | --- |
| `build` | 1 | `1` when `go build ./...` succeeds in `/workspace/repo`, otherwise `0` |
| `no_python` | 1 | `1` when the build succeeds and no `.py` file remains under the repository, otherwise `0` |
| `behaviour` | 4 | Fraction of the 2,000 hidden titles whose output matches, from `0` to `1` |

`reward = (build + no_python + 4 × behaviour) / 6`

## Results

| Run | build | no_python | behaviour | reward |
| --- | --- | --- | --- | --- |
| Oracle | 1 | 1 | 1.0 | 1.0 |
| Nop | 0 | 0 | 0.0 | 0.0 |
| Cheat | 1 | 0 | 0.0 | 0.1667 |

The cheat program ignores stdin and prints the 2,000 memorized practice answers from `tests/data/expected.txt` in their existing order. It deliberately leaves the original Python files in place. That passes the build check and fails both the Python-removal check and the hidden behaviour check, so the reward is `1 / 6 = 0.1667`.

Deleting the Python files as well would make `no_python` 1 while behaviour stayed 0. The same formula would then give `(1 + 1 + 0) / 6 = 0.3333`.

`solution/solve.sh` is the reference port again. It matches `solution/solve.sh.backup-2427968cd9e644e2a82ebc000aa9ad2e` byte for byte. SHA-256: `91c5db4ce06cd206dff6dfb7485759520ff4b4c8e0fda5d14b8b3088b8ddb89e`.

## Screenshots

Place these three captures in `screenshots/`:

![Oracle reward 1.0](screenshots/oracle-reward.png)

![Nop reward 0.0](screenshots/nop-reward.png)

![Cheat reward 0.1667](screenshots/cheat-reward.png)

## Observations

1. The implementation report highlights apostrophe tails and case-sensitive subphrase handling as requiring manual string processing. No record of repeated implementation failures was preserved.

2. A harder variant could expand hidden Unicode cases targeting differences between Python and Go character classification and case conversion, while retaining the same stated behavior.
