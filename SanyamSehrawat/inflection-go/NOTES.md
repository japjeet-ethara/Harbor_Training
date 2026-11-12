# NOTES: inflection-go

Author notes for the Harbor task. The agent never sees this file: it only gets
`instruction.md` and the container built from `environment/`.

## Source

| | |
|---|---|
| Repository | https://github.com/jpvanhal/inflection |
| Commit | `88eefaacf7d0caaa701af7c8ab2d0ab3f17086f1` (2023-03-31T21:03:52+03:00) |
| Version | 0.5.1 |
| Licence | MIT (`LICENSE`, kept in the snapshot) |
| Snapshot | `environment/inflection/`, made with `git archive`, no `.git` |

The task ports 11 functions of `inflection/__init__.py` (12 names, as `camelize` and
`parameterize` are each called two ways). `transliterate` is left out: it needs Unicode NFKD
tables that Go's standard library does not have, so arguments are printable ASCII only.

## Traps: where a first guess is wrong

Each output is what the original really returns (checked against the original).

| Call | Result | Why it surprises |
|---|---|---|
| `pluralize("black sheep")` | `black sheeps` | Uncountables are matched on the whole lower-cased word |
| `singularize("gold fish")` | `gold fish` | ...but `singularize` matches them after a word boundary |
| `pluralize("Roman")` | `Romen` | The `man`/`men` irregular rule ends at `man$`, not at a word start |
| `pluralize("COW")` | `Kine` | Irregulars with different first letters keep only the first letter's case |
| `singularize("KINE")` | `Cow` | Same rule in reverse |
| `singularize("oxenfree")` | `oxfree` | One singular rule has no `$`: `^(ox)en` |
| `camelize("a__b")` | `A_b` | `(?:^|_)(.)` consumes the second `_` as the "letter" |
| `camelize_lower("_a")` | `_a` | `^` matches before `_`, which is then the "letter" |
| `underscore("ABCDefGHI")` | `abc_def_ghi` | Two regexes, greedy acronym split first |
| `titleize("1st place")` | `1St Place` | `str.title()` capitalises a letter after a digit |
| `titleize("they're here")` | `They're Here` | `str.title()` gives `They'Re`; the next regex fixes it |
| `humanize("employee_ID")` | `Employee id` | Only a lower-case `_id` suffix is removed |
| `parameterize("---")` | (empty) | Collapsed to one `-`, then that leading `-` is removed |
| `parameterize_underscore("a-b c")` | `a-b_c` | `-` is an allowed character, so it stays |
| `ordinalize("-0")` | `0th` | `int()` turns `-0` into `0` |
| `ordinalize("007")` | `7th` | Leading zeros disappear |
| `ordinalize("123456789012345678901")` | `123456789012345678901st` | Bigger than 64 bits |

## What makes the task hard

- 56 ordered regex rules plus 8 irregular words that are prepended in a specific order; the
  first matching rule wins, so the order must be exact.
- The two uncountable checks differ (`pluralize` vs `singularize`).
- Python's `str.title()`, `str.capitalize()` and `re.sub` with a function have no direct Go
  equivalent and must be rebuilt.
- `ordinalize` must work on numbers of any size without `math/big` being required.
- As in the original repository layout, a module named `inflection` next to a leftover
  `inflection/` folder makes `go build ./...` fail with "build output already exists and is a
  directory". The instruction requires `go build ./...` to pass, so this is a fair trap.

## Files

| Path | What it is |
|---|---|
| `instruction.md` | The only text the agent reads |
| `task.toml` | Timeouts, resources, non-root agent user, separate offline verifier, artifact hand-over |
| `environment/Dockerfile` | Pinned `golang:1.23` + python3 + the snapshot at `/workspace/repo` |
| `solution/solve.sh`, `solution/port/` | The oracle: installs the Go port, removes the Python code |
| `tests/gen.py` | Makes the input lines and freezes the answers from the original (`random.seed(1)`) |
| `tests/data/` | `inputs.txt`/`expected.txt` (visible) and `hidden_inputs.txt`/`hidden_expected.txt` (graded) |
| `tests/Dockerfile`, `tests/test.sh` | The verifier image (no Python, `/tests` root-only) and entry point |
| `tests/checks/` | The three Reward Kit checks and `reward.toml` |
| `cheat/solve.sh` | A cheat that prints the visible answers, used to prove the tests catch it |
| `scripts/validate.py` | Runs oracle, nop and cheat through Harbor and checks the three rewards |
| `scripts/fuzz.py` | Compares a Linux build of the port with the original on random lines |
| `screenshots/` | Harbor viewer pages for the oracle, nop and cheat runs |

## Scoring

`reward = (1 × build + 1 × no_python + 4 × behaviour) / 6`

| Attempt | build | no_python | behaviour | reward |
|---|---|---|---|---|
| Nothing done | 0 | 0 | 0 | 0 |
| Go code that builds, `.py` files still there | 1 | 0 | 0 | 0.167 |
| Perfect port | 1 | 1 | 1 | 1 |

A program that prints each argument unchanged gets `behaviour` 0.265.

## Validation results

Run on 2026-11-12 with Harbor 0.25.0 and Docker Desktop on Windows (`python scripts/validate.py`;
viewer screenshots in `screenshots/`). The same three results also came out of a run by hand
with the task's two images, without Harbor.

| Run | build | no_python | behaviour | reward | Required |
|---|---|---|---|---|---|
| oracle (reference solution) | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 |
| nop (does nothing) | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| cheat (prints the visible answers) | 1.0 | 0.0 | 0.0 | **0.1667** | below 0.2 |

Other checks:

- `python tests/gen.py` run twice gives identical files; 2,000 lines each; the visible and
  hidden sets share no line.
- The original, run inside the agent image (Debian python3 3.11.2), reproduces all 4,000
  frozen answers.
- The Go port matches the original on all 4,000 frozen lines and on 39,904 random lines
  (`scripts/fuzz.py`).
- `harbor lint --select ALL` reports nothing.

## Known limits

- An empty program plus deleting the `.py` files scores 0.333 (build and no_python pass,
  behaviour is 0), as in the training guide's three checks.
- Third-party source pasted in as a local package cannot be told apart from the agent's own
  code.

## To make the task harder

- Pay `build` and `no_python` only when `behaviour` is above a threshold.
- Add `transliterate` and non-ASCII arguments: NFKD normalisation without `golang.org/x/text`.
