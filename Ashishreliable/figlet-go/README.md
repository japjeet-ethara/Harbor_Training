# figlet-go — Harbor practice task 2

A Harbor task that asks an agent to port [pyfiglet](https://github.com/pwaller/pyfiglet)
to Go. The agent starts with the original Python checkout inside a container that
has no Python, and must reproduce FIGlet rendering byte for byte using only the Go
standard library.

- Repository: `https://github.com/pwaller/pyfiglet`
- Pinned commit: `255827efbc09d662875dad50fa0edc1e1263bf45` (`255827e`, 2026-08-02)
- Licence: MIT
- Author-side tooling: Harbor 0.25.0, Docker Desktop (server 29.9.2), Go 1.23.12

## Overview

The task is deliberately shaped like the practice sheet: the agent inherits a real
Python project, must read it, and then rewrite its behaviour in Go without any
Python available to copy from at run time. Everything the agent needs is inside
`/workspace/repo`; everything that decides the score is outside the image.

What the agent must deliver:

1. A Go program in `/workspace/repo` such that `go build -o /tmp/figlet .`
   produces a CLI with pyfiglet's options: `-f FONT`, `-w COLS`,
   `-j auto|left|center|right`, `-D auto|left-to-right|right-to-left`, `-r`, `-F`,
   `-s`, `-n`, followed by the text.
2. Output that matches pyfiglet byte for byte for those options.
3. `.flf` fonts may be moved, but must stay inside the repository, and the binary
   must work from any working directory.
4. Go standard library only, no `.py` files anywhere in the repository, and
   `go build ./...` must pass.

Not checked: speed, memory use, error-message wording, and the options `-c`, `-L`,
`-l`, `-i`.

The eight exercised font families are `standard`, `slant`, `small`, `big`, `mini`,
`banner`, `shadow`, and `script`.

## Results

Latest runs (2026-11-16):

| Run | Build (1) | No Python (1) | Behaviour (4) | Reward | Secret |
|---|---:|---:|---:|---:|---|
| oracle | 1.000 | 1.000 | 1.000 (2000/2000) | **1.000000** | Drawn |
| nop | 0.000 | 0.000 | 0.000 (0/2000) | **0.000000** | No |
| cheat | 1.000 | 0.000 | 0.000 (0/2000) | **0.166667** | No |

Job records:

| Run | Job directory | Wall time |
|---|---|---:|
| oracle | `jobs/2026-11-16__20-10-10` | 23 s |
| nop | `jobs/2026-11-16__20-14-12` | 16 s |
| cheat | `jobs/2026-11-16__20-16-59` | 44 s |

Verifier output:

```text
oracle  build=1 no_python=1 behaviour=1.000000 reward=1.000000   *** SECRET UNLOCKED ***   behaviour: 2000/2000 matches
nop     build=0 no_python=0 behaviour=0.000000 reward=0.000000   No secret for you. Yet.
cheat   build=1 no_python=0 behaviour=0.000000 reward=0.166667   No secret for you. Yet.
```

The cheat embeds only the 2,000 visible cases, so it builds but answers nothing
from the hidden set. `no_python` is tied to at least one hidden match, so deleting
the `.py` files alone does not earn that point either.

## What the agent sees

`environment/Dockerfile` is a two-stage build:

1. `alpine:3.20` with git: clones pyfiglet at the pinned commit, removes `.git`,
   `fonts-contrib` and `test-fonts`, and applies the Makefile's font setup
   (`pyfiglet/fonts-standard/*` → `pyfiglet/fonts/`).
2. `golang:1.23-alpine` installs `bash` and copies `/src` to `/workspace/repo`,
   owned by the unprivileged `player` user (uid 1000), with `CGO_ENABLED=0` and
   `GOTOOLCHAIN=local`.

The base images are pinned by version tag (`alpine:3.20`, `golang:1.23-alpine`);
digest pinning was left optional, as the practice sheet allows.

Live image checks, run as the task image:

```text
player                   # whoami
1000                     # id -u
/workspace/repo          # pwd
72                       # .flf font files under pyfiglet/fonts
NO_PYTHON_BIN            # no python / python3 on PATH
NO_PYTHON_FILES          # no /usr/bin/python*
/bin/bash
CAN_WRITE                # player can create files
go1.23.12 linux/amd64
```

The image contains no `/tests`, no `hidden.jsonl`, no `visible.jsonl`, no
`grade.go`, no `secret.b64`, and no `solve.sh`; the agent cannot see the answers.

## Grading

`tests/grade.go` runs on the hidden set and writes `/logs/verifier/reward.json`:

```text
reward = (build + no_python + 4 * behaviour) / 6
```

- **build (1):** `go build -o /tmp/figlet .` in `/workspace/repo`.
- **no_python (1):** build passed, no `.py` file anywhere under `/workspace/repo`,
  and at least one hidden case matches.
- **behaviour (4):** share of the 2,000 hidden cases whose stdout matches the
  expected `out` exactly, 5 s per case with an 8-minute global deadline.

If behaviour is exactly 1.0, the grader decodes `tests/secret.b64` and renders it
with `-f slant` after printing `*** SECRET UNLOCKED ***`. Otherwise it prints
`No secret for you. Yet.`

## Test data

`tests/gen.py` runs on the author's machine, with the Step 1 pyfiglet checkout next
to the task folder. Every expected output comes from `pyfiglet.main()`; nothing is
hand-written.

- `random.seed(7)`
- 2,000 visible + 2,000 hidden cases, one JSON object per line
- argument sets are completely disjoint between the two files (0 overlap)
- two fresh runs are byte-identical and match the frozen files:

```text
64baad41ae72f00cc9781f91e4290d2b15f5e42bdc96dcec74f6ac91f40b5b27  visible.jsonl
f56493ad0a2af41fc5adb65333b4e379ec7fe3395396294e6c20dc85b2cf62af  hidden.jsonl
```

Hidden-set coverage: 617 explicit right-to-left, 605 left-to-right, 778 auto
(576 explicit + 202 default); 261 cases at width 10 and 289 at width 20;
438 non-ASCII, 119 newline, 107 blank, and 129 containing rare bracket/pair
classes (`[]`, `{}`, `()`, `<>`, `/\`). Per font: `mini` 463, `big` 212,
`script` 210, `banner` 197, `slant` 196, `standard` 192 + 175 default, `small`
182, `shadow` 173.

## Requirements checklist

Mapping of the practice sheet's self-check to this task:

| Requirement | Status | Where |
|---|---|---|
| `NOTES.md`: URL, SHA, date, MIT, font setup step, six smushing rules | Done | `NOTES.md` — all six rules with examples, plus kerning, full-width, and the eight options |
| Image: two stages, Alpine Go, `bash`, user `player`, `NO_PYTHON`, pinned | Done | `environment/Dockerfile`; live checks above |
| `instruction.md`: every sentence testable, no secret, no test names | Done | `instruction.md`, 493 words; no secret, test names, or example cases |
| `gen.py`: seeded, answers from the original only, same output twice | Done | `tests/gen.py`, seed 7; double-run hashes match the shipped data |
| Grader in Go: build 1, no_python 1 tied to a right answer, behaviour 4 on hidden cases | Done | `tests/grade.go`; `no_python` requires `matches > 0`; formula above |
| Oracle 1.0 with the secret drawn; nop 0.0; cheat below 0.2 with no secret | Done | rows in the Results table |
| Real screenshots and two honest lines | Done | `screenshots/oracle.png`, `nop.png`, `cheat.png` (+ `oracle-secret.png`); honest lines below |

## Verified integrity checks

- Visible and hidden argument sets are disjoint (0 overlap), so the cheat cannot
  score from the visible file.
- The built image has no access to the test data; `/tests` does not exist there.
- The Step 8 page-secret check was run inside the image as `player`, after the
  oracle, and rendered cleanly in `slant`. The exact command is in the practice
  sheet.
- `harbor lint figlet-go` reports only `shared-verifier`, which the practice sheet
  accepts for this task.
- The oracle's hidden score is 2000/2000 with all four components at 1.0, so the
  documented reward and the printed secret come from the same run.

## Two honest lines

**Smushing rule that broke the most:** none of the six broke — the first Go port
matched 4,000/4,000 local cases. The rule that needed the most care was
hierarchy/opposite-pair (`[]`, `{}`, `()` → `|`), because a wrong class order is
invisible except on rare adjacent pairs.

**Docker trap hit:** none of the three sheet traps — Alpine Go has no Python, bash
is installed explicitly, and stage 1 clones pyfiglet. The real trap was in data
generation: pyfiglet never returns when a glyph is exactly as wide as `-w`, so
width 10 forces `mini`.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | Task contract for the agent (493 words). |
| `task.toml` | Harbor configuration: `player` user, 900 s verifier, 3600 s agent. |
| `environment/Dockerfile` | Two-stage room; pyfiglet source + Go 1.23, no Python. |
| `solution/solve.sh` | Oracle: writes the Go port, embeds eight fonts, deletes `.py`, builds. |
| `cheat/solve.sh` | Memorised visible answers only; proves the hidden set catches it. |
| `tests/grade.go` | Grader; writes `reward.json`, prints the secret on 2000/2000. |
| `tests/test.sh` | `cd /tests && go run grade.go`. |
| `tests/gen.py` | Deterministic case generator. |
| `tests/data/` | 2,000 visible + 2,000 hidden frozen cases. |
| `tests/secret.b64` | `nice port, human`. |
| `screenshots/` | Real terminal captures: `oracle.png`, `nop.png`, `cheat.png`, and the bonus `oracle-secret.png`. |
| `NOTES.md` | Repo facts, font setup, smushing rules, option semantics. |

## Reproduce

```bash
harbor run -p ./figlet-go -a oracle
harbor run -p ./figlet-go -a nop

# cheat: back up solution/solve.sh, copy cheat/solve.sh over it,
# run the oracle command, then restore the real solution.
cp figlet-go/solution/solve.sh /tmp/solution.solve.sh
cp figlet-go/cheat/solve.sh figlet-go/solution/solve.sh
harbor run -p ./figlet-go -a oracle
cp /tmp/solution.solve.sh figlet-go/solution/solve.sh
```

The real solution restores to
`sha256 48acc5fe62eebb9b70c78dd9b4849a4615338d31990eeb850d884f8594bc3f1f`.

## Screenshots

The three required real terminal captures live in `screenshots/`:

| File | Run | Must show |
|---|---|---|
| `oracle.png` | `harbor run -p ./figlet-go -a oracle` | all four scores `1.000`, `2000/2000 matches`, `*** SECRET UNLOCKED ***`, slant banner |
| `nop.png` | `harbor run -p ./figlet-go -a nop` | all four scores `0.000`, `No secret for you. Yet.` |
| `cheat.png` | cheat `solve.sh` in place, then the oracle command | build 1, no_python 0, behaviour 0, `0.166667`, `No secret for you. Yet.` |

`screenshots/oracle-secret.png` is an extra capture of the unlocked secret banner.
