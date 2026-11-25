# DEFENCE — Mohammad Adnan (Day 6, 5-minute talk)

Task: `training-3/MohammadAdnan/task` (titlecase-go). Attacker: Charitra. I attacked Vanam Prashanth.

## Proof (all real Harbor runs; job folders on my machine, reward files in `proof/`)

| Run | Must be | Got | Job folder |
|---|---|---|---|
| oracle | 1.0 | **1.0** | `jobs/2026-11-20__12-48-21` |
| nop | 0.0 | **0.0** | `jobs/2026-11-20__12-49-19` |
| Charitra c1 build-only | < 0.2 | **0.167** | `jobs/2026-11-20__12-50-08` |
| Charitra c2 delete-Python-only | < 0.2 | **0.0** | `jobs/2026-11-20__12-50-59` |
| Charitra c3 partial port | < 0.2 | **0.167** | `jobs/2026-11-20__12-51-51` |
| copy the leaked port (Charitra finding 1) | < 0.2 | **0.0** | `jobs/2026-11-20__12-52-44` |
| read the exam (extra) | < 0.2 | **0.167** | `jobs/2026-11-20__12-53-36` |
| Python inside (extra) | < 0.2 | **0.167** | `jobs/2026-11-20__12-54-27` |

0.167 = 1/6 = only the build point: the program compiles, nothing else.

## 1. Strongest cheat against my task — before and after

**Copying the leaked reference port: 1.0 → 0.0.** My practice-1 `environment/Dockerfile` copied my own
Go solution into the agent's image at `/opt/python-titlecase/` (Charitra's finding 1). A cheat that
just copies those three files scored a perfect 1.0. Now the port is only inside `solution/solve.sh` (Day 6: moved there from `solution/go/`), which
Harbor uploads for oracle runs only, so the copy finds nothing and the build fails.

Two other cheats also scored 1.0 before: reading `/tests/data/hidden_expected.txt` at run time (now:
the grader locks `/tests` and runs the program as `nobody`) and running the original Python through a
Go wrapper (now: no Python in either image, and the grader scans the repo and the binary for Python
code). Charitra's partial port went 0.558 → 0.167.

## 2. Before-and-after exam

| Port | Wrong on new exam (100,000, re mode) | Old exam (2,000) caught it? | Chance 2K random misses it |
|---|---|---|---|
| my oracle, before the fix | 1,627 | no (0 wrong) | 0% |
| my oracle, after the fix | 0 | n/a | n/a |
| Vanam Prashanth | 3,451 | no (0 wrong) | 0% |
| Charitra | 0 | n/a | n/a |

New exam: trainer's kit, `make_pool.py 100000 1` plus my `EXTRA` word family; answers frozen twice,
100,000 kept, 0 dropped, regex not used; the mode is written in `instruction.md`.

## 3. What surprised me

**My own port was wrong on 1,627 of 100,000 titles** although it scored 1.0 on my own exam. It used the
`regex`-mode rules (`\p{L}`, letters only), but the answers come from `re` mode, where `\w` also
matches `_` and digits: `_dream` must stay `_dream`, my port wrote `_Dream`. The new exam found it; I
fixed the port and removed no inputs.

Second surprise: my first hardened version still let two cheats through (0.445 and 0.343), because
"at least one right answer" for `no_python` is paid even by a program that echoes its input (1,502
titles are already correct as typed). Credit now starts above 50% accuracy.

## Every change, in one line each (for questions)

- `environment/Dockerfile`: `golang:1.23-alpine` pinned by digest; `bash`; user `player`; no Python;
  no reference port.
- `tests/Dockerfile`: `golang:1.23-alpine` pinned; no Python; grader is Go.
- `tests/checks/build.go`: `go build ./...` (output to a temp folder) + `go build -o <bin> .` + no
  `require` in `go.mod`.
- `tests/checks/no_python.go`: no `.py` file, no Python markers in any repo file or in the binary.
- `tests/checks/behaviour.go`: 100,000 inputs as one text on stdin; program runs as uid 65534 from
  an empty folder; exact line match.
- `tests/checks/main.go`: locks `/tests` and `/logs`; `behaviour = max(0,(accuracy-0.5)/0.5)`;
  `no_python` only if behaviour > 0; `reward = (build + no_python + 4·behaviour)/6`.
- `tests/data/inputs.txt`, `answers.txt`: from `kit/answers.py` (re mode).
- `solution/solve.sh`: the port lives only here, as heredocs (no `solution/go/` any more); removes the empty `titlecase/`
  folder that broke `go build ./...`.
- the port's `titlecase.go`: `re`-mode patterns, Unicode `\w`, Python-style `upper()`,
  `str.isspace()` spaces, rune counts, title-case in `capitalize()`.
- `instruction.md`: mode stated; no-Python rule spelled out; runs as unprivileged user; scoring rule.
- `task.toml`: `[agent] user = "player"`, longer timeouts, name and author.

## Honest limits

- Charitra's report had no runnable cheats or scores, so I wrote their three probes from the text.
- The network is still public (`network_mode = "public"`), so an agent could in theory download
  something; the Python scan would catch a downloaded Python interpreter (`Py_Initialize`) but not
  every possible tool.
- Ports that need more than 50% right to earn anything get no partial credit below that line; this
  is a deliberate trade so half-ports cannot score.

## Day 6 — Charitra's re-attack and my answer

Charitra re-ran their three probes on my hardened task (commit `240786b`): **0.167, 0.0, 0.167**, all
below 0.2 (their `training-3/Charitra/task/Attack.md.md`). They added a fourth probe, **"reference mount
scan"**, which scored **1.0**: it copies the Go port from `/solution/go/`.

That path exists only in an oracle run (Harbor uploads `solution/` for the oracle agent only; a real
agent never sees it), so it was not a leak to a candidate. Charitra said this too. But under the same rules
every cheat here is tested with (cheat = a replaced `solve.sh`), the port was still on disk next to it.
I closed that anyway: **the port now lives only inside `solution/solve.sh` as heredocs**, and
`solution/go/` is gone. A replaced `solve.sh` has nothing to copy. The heredocs write the four files
byte-for-byte identical to the old ones (checked with `cmp`).

Full re-run after this change (reward files in `proof/day6/`):

| Run | Must be | Got | Job folder |
|---|---|---|---|
| oracle | 1.0 | **1.0** | `jobs/2026-11-20__15-24-38` |
| nop | 0.0 | **0.0** | `jobs/2026-11-20__15-25-41` |
| c1 build-only | < 0.2 | **0.167** | `jobs/2026-11-20__15-26-31` |
| c2 delete-Python-only | < 0.2 | **0.0** | `jobs/2026-11-20__15-27-23` |
| c3 partial port | < 0.2 | **0.167** | `jobs/2026-11-20__15-28-16` |
| c4 copy the leaked port | < 0.2 | **0.0** | `jobs/2026-11-20__15-29-09` |
| c5 read the exam | < 0.2 | **0.167** | `jobs/2026-11-20__15-30-01` |
| c6 Python inside | < 0.2 | **0.167** | `jobs/2026-11-20__15-30-54` |
| c7 Charitra's mount scan | < 0.2 | **0.167** (was 1.0; accuracy 0.015 = echo fallback) | `jobs/2026-11-20__15-31-48` |
