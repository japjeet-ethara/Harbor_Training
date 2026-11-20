# my-org/titlecase-go

Harbor task: port [python-titlecase](https://github.com/ppannuto/python-titlecase)
(commit `42f43e2`, MIT) to Go, with output identical to the Python byte for byte.

## Layout

| Path | Seen by agent? | What it is |
|---|---|---|
| `instruction.md` | yes | The question paper |
| `environment/Dockerfile` | yes (it *is* the room) | golang:1.23 (pinned) + python3 + regex, repo at `/workspace/repo`, examples at `/workspace/examples`, non-root user `agent` |
| `environment/python-titlecase/` | yes | Copy of the repo without `.git` |
| `environment/examples/` | yes | Visible 2000 inputs + answers |
| `solution/solve.sh`, `solution/main.go` | no | The oracle: a full Go port |
| `tests/` | no | Verifier: own container (`tests/Dockerfile`), Reward Kit checks, hidden answers |
| `tests/data/` | no | `inputs/expected` (visible copy) and `hidden_inputs/hidden_expected` |
| `tools/gen.py` | no (author only) | Makes the four data files from the ORIGINAL Python |
| `tools/compare.py` | no (author only) | Shows the first 10 differing lines |
| `cheat/solve.sh` | no (author only) | Prints the visible answers. Proves the tests catch it |

## Scoring (`tests/reward.toml`, weighted mean)

| Check | Weight | Passes when |
|---|---|---|
| `build` | 1 | `go.mod` exists with no `require` lines and `go build -o <tmp>/ ./...` passes |
| `no_python` | 1 | no `.py` files under `/workspace/repo` **and** the build passes |
| `behaviour` | 4 | share of the 2000 hidden titles printed exactly right |

## Rewards from real Harbor runs (Docker, 18 Nov 2026)

| Run | build | no_python | behaviour | reward |
|---|---|---|---|---|
| nop (do nothing) | 0 | 0 | 0 | **0.0** |
| build only (local check, not a Harbor run) | 1 | 0 | 0 | 0.17 |
| cheat (`cheat/solve.sh`) | 1 | 0 | 0 | **0.17** (< 0.2) |
| oracle (`solution/solve.sh`) | 1 | 1 | 1.0 | **1.0** |

The Go port was also fuzzed against the original on 60,000 extra random titles:
60,000/60,000 matched.

## What makes it hard

- Python's `str.upper()` turns `ß` into `SS`, but Go's `unicode.ToUpper` leaves it as `ß`.
  This affects both the "is the line all caps" test and capitalisation.
- `UC_ELSEWHERE` / `CAPFIRST` use a lazy punctuation prefix (`*?`), and
  `SMALL_LAST` combines `\b` with `$`. None of these exist in Go's RE2.
- `SUBPHRASE` is case-sensitive and has no word boundary, so `title: android`
  becomes `Title: Android` (it matches the small word `a`).
- The order of the alternatives (`v\.?` before `via`, `a` before `and`) decides which match wins.
- The library falls back to `re` if `regex` is missing, and then gives different answers.

## Known weakness (idea for hardening)

A cheat that also deletes the `.py` files scores 0.33. To close that gap,
make `build` and `no_python` pay only when `behaviour` is above, for example, 0.5,
or weight `behaviour` higher.

## Lesson from the first oracle run

The first oracle run scored 0.667, not 1.0. A bare `go build ./...` on a single
main package writes a binary named after the module (`titlecase`) into the
repo, and that collided with the leftover `titlecase/` Python folder. The tests
now build into a temporary folder, and the oracle removes empty folders.
Windows didn't catch it, because Go writes `titlecase.exe` there. That's
exactly why the oracle has to run in the real container.
