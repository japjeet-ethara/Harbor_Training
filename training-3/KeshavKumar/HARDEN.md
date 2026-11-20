# HARDEN — KeshavKumar's `titlecase-go`

Attacker: Utkarsh Gupta (`training-3/Utkarsh Gupta/attack/ATTACK.md`).
All runs: `harbor run -p <copy of task> -a oracle` (cheats copied over `solution/solve.sh`),
Harbor 0.25.0, local Docker. Job folders are under `KeshavKumar/jobs/` (not pushed).
"Before" = task as pushed in `copy practice task before hardening`; "after" = this commit.

I re-ran the attacker's three cheats, plus my own three cheats from `attack/` (written for
Utkarsh's task, and they also apply here). Two of mine scored **1.0** on my old task.

## Holes closed

| Cheat | Before | After | Job folders (before → after) |
|-------|--------|-------|------------------------------|
| U1 — read the exam (attacker) | 0.1667 | 0.1667 | `before-U1__RUwx7BC` → `after-U1__i6tndBp` |
| U2 — half port (attacker) | **0.3233** | 0.1667 | `before-U2__wYyYtG9` → `after-U2__R52yzb9` |
| U3 — empty program + delete `.py` (attacker) | 0.1667 | 0.1667 | `before-U3__XePMzAd` → `after-U3__ByQYaXG` |
| K1 — read the exam (mine) | **1.0** | 0.1667 | `before-K1__cPHUnAp` → `after-K1__8wZE5wU` |
| K2 — Python inside (mine) | **1.0** | 0.1667 | `before-K2__RJmRiwU` → `after-K2__toSzwvn` |
| K3 — fake `python3` for the grader (mine) | 0.1667 | 0.1667 | `before-K3__x7Rok8E` → `after-K3__82eX5AX` |
| oracle | 1.0 | **1.0** | `before-oracle__hJbnhAH` → `after-oracle__ckoEcGr` |
| nop | 0.0 | **0.0** | `before-nop__mNKwJPT` → `after-nop__PdNv4TB` |

The remaining 0.1667 for every cheat is the `build` check (weight 1 of 6): an empty Go
program does build. It is below 0.2 and it is a real, independent check, so I kept it.

**U1 — the attacker's report is right about the score, wrong about the reason.** ATTACK.md says
the cheat failed because `/tests` is not in the container where the binary runs. That is not
true: my grader built and ran the binary *in the verifier container*, next to `/tests`. The
cheat failed because of a bug in the cheat itself: both `bufio.Scanner`s share one buffer
(`inSc.Buffer(buf, …)` and `exSc.Buffer(buf, …)`), so each read overwrites the other and every
lookup key is wrong. Run offline on my old hidden files, the cheat as written matched 0/2000;
with only that line changed to a second buffer it matched **2000/2000**. My K1 (no bug) scored
1.0 in Harbor. So the hole was real.

Fixes, and which cheat each one closes:

| Fix | File | Closes |
|-----|------|--------|
| The agent's program runs as `nobody` (uid 65534). The grader reads the answers into memory *first*. `test.sh` and `tests/Dockerfile` make `/tests` mode 700, and `test.sh` makes `/logs/verifier` mode 700. After the run, every process left by `nobody` is killed (`kill -KILL -1` sent as nobody). | `tests/common.py` `_behaviour_share`, `_kill_leftovers`; `tests/test.sh`; `tests/Dockerfile` | K1, U1 (fixed or not) |
| No Python where the program runs: system `python3` purged from the verifier image; Reward Kit's own Python is uv-managed under `/root` (mode 700), unreachable for `nobody`. Also purged from the agent image, so the original cannot be run to make answers. | `tests/Dockerfile`, `environment/Dockerfile` | K2 |
| Behaviour credit starts above a 50% floor: `(share − 0.5) / 0.5`, 0 at or below 50%. A port that gets half the titles wrong is not a port. 100% → 1.0, 99% → 0.98, 75% → 0.5. Stated in `instruction.md`. | `tests/common.py` `behaviour_credit`, `tests/behaviour/check.py` | U2 (16.2% right on the new exam → credit 0) |
| No network while the agent works (`[agent] network_mode = "allowlist"`, only the model endpoint) and none while it is graded (`[verifier] network_mode = "no-network"`). The answer files are on public GitHub, so open internet = free answers. Reward Kit is now baked into the verifier image so grading works offline. | `task.toml`, `tests/Dockerfile`, `tests/test.sh` | "download the answers" (new) |
| `go build` runs as root, so it now runs with `CGO_ENABLED=0`, `GOTOOLCHAIN=local`, `GOPROXY=off`: no cgo, no toolchain download, no module proxy. | `tests/common.py` `_BUILD_ENV` | defence in depth |
| K3 (fake `python3`) was already closed by the separate verifier container; still 0.1667. | — | K3 |

**Proof the protections really work** — `kit/probe_solve.sh`, run as a solution
(`after-probe__wgYB2ND`). While the agent works it records its own view; its Go program prints what
it can reach while graded, which lands in `verifier/behaviour_mismatches.txt`:

```
agent phase : uid=0(root); python3: none; HTTPS to raw.githubusercontent.com and pypi.org: SSL_ERROR_SYSCALL
graded as   : uid=65534 gid=65534
read /tests/data/answers.txt: permission denied     list /tests: permission denied
list /root: permission denied                       python3: not found anywhere
write /logs/verifier: permission denied
tcp github.com:443 (connect only): OK               <- Harbor's egress sidecar accepts the connect...
GET https://raw.githubusercontent.com/...: EOF       <- ...but no data passes
GET http://example.com/: EOF
```

## Exam: before and after

Old exam: 2,000 hidden inputs from my `gen.py`. New exam: **100,000** inputs, mode: **re**
(titlecase WITHOUT the `regex` package), stated in `instruction.md`.

How the new exam was made (`kit/`; Linux `python:3.14-slim` container, so line endings are `\n`):

```
python -I kit/make_pool.py 100000 1 pool.txt
python -I kit/answers.py task/environment/repo pool.txt key     # runs the original twice
```

`kit/report.txt`: 100,000 in, 100,000 kept, 0 dropped, `regex module used False`.

`kit/make_pool.py` is the trainer's script with one change: an extra word bank (and three more
sub-phrase separators) with families my old exam had and the trainer's pool did not. The reason
is in the table below: SakshiSingh's port is perfect on the trainer's pool but not on my old exam.
With the trainer's unchanged script and seed 1, my answers are byte-identical to AnnuKumari's
(same md5), so the freeze itself is reproducible.

| Port | Wrong on new exam (100K, my pool) | Wrong on trainer's pool (100K) | Old exam (2K) caught it? | Chance a random 2K from new exam misses it |
|------|------|------|------|------|
| my oracle | 0 | 0 | n/a (0 of 2,000 wrong) | n/a |
| SakshiSingh | **1,701** | 0 | yes (4 of 2,000: `İSTANBUL` → `Istanbul`) | 0% |
| Utkarsh Gupta | 18,508 | 13,275 | yes (252 of 2,000) | 0% |

Files: `measure/<port>.txt` (new exam), `measure/plain-kit-pool/<port>.txt`,
`measure/old-exam/<port>.txt` — all `compare.py` output. Ports were built with
`go build` in `golang:1.23`, `--network none`, and fed the inputs on stdin.
SakshiSingh's port = her `solution/go.mod` + `main.go`; Utkarsh's = Go files written by running his
`solution/solve.sh` (offline) on the original repo.

SakshiSingh's bugs that only the new families find: letters whose capital is more than one
character (`ŉ` → `ʼN`, `ﬂow` → `FLow`), and the dotted capital `İ` in all-caps lines.

## What I learned

1. A separate verifier container stops tampering, not reading: the agent's program runs *inside*
   the grader, so it must run as a user that cannot see the answers.
2. "Python is not allowed" only holds if Python is not installed — `golang:1.23` ships `python3`.
3. Weird beats big: 100,000 titles from the trainer's pool missed a bug that 4 of my 2,000 old
   titles caught, because the pool never contained `İ`. Adding the missing families found 1,701.
