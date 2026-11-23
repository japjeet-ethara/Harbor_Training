# Day 5 Report — Hardening the Task

Target: `titlecase-go` (`test/titlecase-go`), hardened in place under
`training-3/ShivamTiwari/task/`.

Everything below is measured. The "before" numbers are the scores recorded in
the Day 4 attack report; the "now" numbers are real Harbor runs executed on
2026-11-20 with the hardened task.

## Reconstruction note

The attack report names three job folders (`jobs/2026-11-19__14-5*`) for the
original cheats, but those folders and scripts were not present in this
workspace. `proof/cheats/cheatN/solve.sh` therefore reproduce the mechanisms
described in the report, and the reruns are labelled as reconstructions. They
are not presented as the attacker's lost files.

## Holes closed

### Cheat 1 — Python inside

- **Before:** 1.0 (build 1, no_python 1, behaviour 1)
- **Now:** 0.0000 (build 0, no_python 0, behaviour 0)
- **Job folder:** `harden-runs/jobs/cheat1-hardened` (trial `cheat1__PPAe6GV`)
- **Weakness:** `tests/no_python.py` only looked for file names ending in `.py`,
  and `tests/Dockerfile` was `FROM python:3.12-slim`, so `/usr/local/bin/python3`
  stayed executable while the Go binary called it at runtime.
- **Fix:**
  - `tests/Dockerfile` now builds on `golang:1.23`, adds an unprivileged
    `runner` user, and runs `chmod 700 /usr/bin/python* /usr/local/bin/python*`
    so the submitted binary cannot start an interpreter.
  - `tests/checks/no_python.py` no longer trusts file names. It rejects Python
    suffixes, embedded Python source markers (`def titlecase(`, `import regex`,
    `/usr/bin/python`, …), interpreter binaries (`Py_Initialize`, `libpython`),
    `//go:embed`, cgo, `os/exec`, `syscall`, `plugin`, `unsafe`,
    `os.StartProcess`, `exec.Command`, and any `require` line in `go.mod`.
  - It also proves at runtime that `runner` cannot launch `python3`, and it
    requires 98% exam accuracy before awarding the point.
- **Evidence:** the reconstructed binary compiles, but every structural and
  behavioural check is zero. `//go:embed` plus `os/exec` are rejected statically
  and the interpreter is unreachable at runtime, so the program exits non-zero
  and behaviour is 0.

### Cheat 2 — Half port

- **Before:** 0.453 (build 1, no_python 1, behaviour 0.1795)
- **Now:** 0.0036 (build 0, no_python 0, behaviour 0.0055)
- **Job folder:** `harden-runs/jobs/cheat2-hardened` (trial `cheat2__GYNpSJY`)
- **Weakness:** `tests/behaviour.py` gave linear partial credit
  (`matches / len(expected)`) with no floor, `tests/gen.py` weighted simple
  words three times higher than edge cases, and `build`/`no_python` paid out on
  a program that only compiled.
- **Fix:**
  - `tests/checks/behaviour.py` keeps fractional credit but gates it: full
    credit needs **≥ 0.98 overall** and **≥ 0.95 edge-case** accuracy
    (apostrophes, Mc/Mac, honorifics, acronyms, inline periods, slashes,
    hyphens, underscores, versions, tabs, NBSP, Unicode, subphrase punctuation).
    Below either floor the value is multiplied by **0.10**.
  - `build` and `no_python` each require ≥ 0.98 exam accuracy, so structural
    points cannot be collected by a stub.
  - The new pool is **98.63%** edge-classified (98,627 / 100,000 lines), so the
    old "normal words dominate" weighting is gone.
- **Note:** the reconstruction is even weaker than the reported port (raw
  accuracy 5.5% versus 17.95%). That does not change the conclusion: at 17.95%
  raw accuracy the gated reward would be `0.1795 × 0.10 × 4/6 = 0.0120`
  (arithmetic on the reported number, not a separate measurement).

### Cheat 3 — Delete trick plus public notes lookup

- **Before:** 0.3883 (build 1, no_python 1, behaviour 0.0825)
- **Now:** 0.0022 (build 0, no_python 0, behaviour 0.0034)
- **Job folder:** `harden-runs/jobs/cheat3-hardened` (trial `cheat3__BQosQTy`)
- **Weakness:** `tests/build.py:14-16` and `tests/no_python.py:23-27` awarded
  `2/6` unconditionally for compiling a stub after deleting `.py` files, and
  `tests/gen.py` copied 104 `NOTE_LINES` into `hidden_inputs.txt`, so a lookup
  table of public examples scored.
- **Fix:**
  - No structural point without 98% behaviour (both checks now run the exam).
  - The old generator was moved out of the task to
    `kit/evidence/old-exam-2000/`; `task/tests/` no longer generates or leaks
    anything.
  - The new 100,000-line exam has **zero** exact overlap with the 22 public
    `NOTES.md` example inputs and **zero** exact overlap with the 73
    `titlecase/tests.py` `TEST_DATA` inputs. The lookup table knows 23 lines and
    therefore scores 3.4% on the other 99,977.
  - The answer file lives in `task/tests/data/`, which is never part of the
    agent image: `environment/Dockerfile` copies only
    `environment/python-titlecase` into `/workspace/repo`.

## Exam: before and after

| Property | Old exam | New exam |
|---|---|---|
| Size | 2,000 lines | 100,000 lines |
| Generator location | `task/tests/gen.py` (shipped inside the task) | `kit/` (outside the task) |
| Reference mode | `re` and `regex` both matched the old set | `re` (`REGEX_AVAILABLE = False`), documented in `instruction.md` |
| Generated inputs | 2,000 | 100,000 unique (seed 1) |
| Stable inputs kept | 2,000 | 100,000 (reference run twice per line, 0 dropped) |
| Public-example leakage | 104 `NOTE_LINES` copied into the hidden inputs | 0 overlaps with `NOTES.md` (22 inputs) and `TEST_DATA` (73 inputs) |
| Edge-case share | simple words weighted 3× | 98,627 edge lines (98.63%) |

`task/tests/data/inputs.txt` sha256
`cd31c3c6aef6eb95258b96363726b7161603d33f22c6a443030d60863e3f56a3`;
`task/tests/data/answers.txt` sha256
`e36ab802aa70ca69fb8056cac50452ba32851945772d13fba412c283fcd17102`.

## Comparison table

Each port was extracted from that port's own `solution/solve.sh`, built inside
`golang:1.23` (`GOTOOLCHAIN=local CGO_ENABLED=0`), fed the exam inputs on stdin,
and compared byte for byte. "Old exam" is the archived 2,000-line hidden exam in
`kit/evidence/old-exam-2000/`.

| Port | Wrong answers (new exam) | Old exam result | New exam result |
|---|---|---|---|
| My Oracle | 0 | 0 / 2000 wrong (100.00%) | 0 / 100000 wrong (100.00%) |
| Port A | 0 | 0 / 2000 wrong (100.00%) | 0 / 100000 wrong (100.00%) |
| Port B | 0 | 0 / 2000 wrong (100.00%) | 0 / 100000 wrong (100.00%) |

Port A and Port B are anonymised classmates' Go ports. All three saturate the
new exam because the pool was generated with the prescribed script and seed that
the whole cohort used for calibration. Saturation is not a weakness of the exam
for this task: the reward is a threshold, and what matters is that incomplete
implementations (cheats 2 and 3) fall far below a complete port.

## Validation

| Run | Command | Reward | Job |
|---|---|---|---|
| Oracle | `harbor run -p task -a oracle` | 1.0000 | `harden-runs/jobs/oracle-hardened` (`task__nXsWFVH`) |
| Do nothing | `harbor run -p task -a nop` | 0.0000 | `harden-runs/jobs/nop-hardened` (`task__gXicSUV`) |
| Cheat 1 | `harbor run -p <scratch> -a oracle` | 0.0000 | `harden-runs/jobs/cheat1-hardened` |
| Cheat 2 | `harbor run -p <scratch> -a oracle` | 0.0036 | `harden-runs/jobs/cheat2-hardened` |
| Cheat 3 | `harbor run -p <scratch> -a oracle` | 0.0022 | `harden-runs/jobs/cheat3-hardened` |

Oracle component scores: behaviour 1.0 (100,000/100,000), build 1.0,
no_python 1.0. The oracle run is also the build validation: the real Go program
compiles inside the Python-free verifier image and reproduces the exam exactly.

`proof/` contains the verifier reward JSON for the oracle and nop runs, and
`proof/cheats-reward.txt` records the three cheat reruns.

## Round 2 — re-attack hardening (2026-11-20)

Annu Kumari's `attack/ATTACK.md` is byte-for-byte the same three-cheat report
that round 1 closed: same target SHA (`8a12385d…`), same reported scores
(1.0 / 0.453 / 0.3883). Round 2 therefore targets what a re-attack would find,
rather than re-fixing the same three scripts.

### What was still open after round 1

The round-1 rules were enforced only inside `no_python`. `build` and
`behaviour` never ran the rule scan, and the verifier made the Python
*executables* unreadable but left the standard library world-readable. A
submission that

1. copied `/usr/bin/python3.11` into `/workspace/repo/pybin`,
2. kept the reference source as a plain-text asset, and
3. ran the copy with `os/exec`

kept perfect behaviour and the build point. Measured against the round-1 task:
**0.8333** (build 1, no_python 0, behaviour 1.0). That is the residual hole.

### Round-2 changes

- **One gate for all criteria.** `tests/checks/_common.py` now owns `audit()`
  and `exam()`; `build`, `no_python` and `behaviour` all call them. A
  structural violation is worth 0 everywhere instead of 5/6.
- **Authoritative import graph.** `go list -deps` resolves every reachable
  package belonging to the submitted module. Raw-string (``import `os/exec` ``),
  escaped (`"os\x2fexec"`) and aliased (`import e "os/exec"`) spellings all
  canonicalise to the same path. Direct `syscall`/`unsafe` are banned per local
  package (the stdlib itself reaches them, so only submitted packages are
  checked there); `os/exec`, `plugin`, `net*`, `golang.org/x/sys`, `embed` and
  `runtime/cgo` are banned transitively. Packages under `_hidden/`, which the
  `./...` wildcard skips, are still inspected because they are reachable.
- **Alias-proof symbol bans.** `StartProcess`, `ProcAttr`, `exec.Cmd`,
  `exec.LookPath`, `syscall.Syscall`, … are rejected as bare names, so
  `import o "os"; o.StartProcess(...)` is caught.
- **Sealed standard library.** The verifier also runs
  `chmod 700 /usr/lib/python3* /usr/local/lib/python3* …/libpython*`. A copied
  interpreter starts but cannot find `encodings`, so it cannot run.
- **Pinned build environment.** `GO111MODULE=on`, `GOTOOLCHAIN=local`,
  `GOWORK=off`, `GOPROXY=off`, `CGO_ENABLED=0`.
- **Expanded file rules.** Foreign/native extensions (`.s`, `.syso`, `.o`, `.a`,
  `.so`, `.dll`, `.c`, `.h`, `.cpp`, `.wasm`, …), other runtimes (`.js`, `.pl`,
  `.rb`, `.php`, `.lua`, `.jar`, …), symlinks (files and directories),
  `vendor/`, `go.work`, `require`/`replace`/`toolchain`, and files over 64 MB
  are rejected.

### Round-2 measurements

| Attempt | Round-1 task | Round-2 task |
|---|---|---|
| Oracle (real Go port) | 1.0000 | 1.0000 |
| Do nothing | 0.0000 | 0.0000 |
| Annu cheat 1 (embed + `os/exec`) | 0.0000 | 0.0000 |
| Annu cheat 2 (half port) | 0.0052 | 0.0052 |
| Annu cheat 3 (delete + NOTES lookup) | 0.0022 | 0.0022 |
| Copied interpreter (new, `cheat4`) | 0.8333 | 0.0000 |

The two non-zero residuals are below-floor behaviour credit (10% of raw
accuracy); `build` and `no_python` are 0 for both, so neither can exceed 0.5%.

Ann's three scripts were run exactly as committed (line endings normalised to
LF for bash) against scratch copies of the pre-round-2 task and of the round-2
task. The copied-interpreter attack is mine (`proof/cheats/cheat4/solve.sh`),
because it is the hole a re-attack would naturally reach for. Job folders:
`harden-runs/jobs/*-before*` and `harden-runs/jobs/*-final`.

| Run | Job | Trial | Reward |
|---|---|---|---|
| Oracle | `oracle-final` | `task__EtFCBdB` | 1.0000 |
| Do nothing | `nop-final` | `task__eKGotkQ` | 0.0000 |
| Annu cheat 1 | `annu-cheat1-final` | `annu-cheat1__SNZh2na` | 0.0000 |
| Annu cheat 2 | `annu-cheat2-final` | `annu-cheat2__cHxeAgH` | 0.0052 |
| Annu cheat 3 | `annu-cheat3-final` | `annu-cheat3__TZ2rt6e` | 0.0022 |
| Copied interpreter | `cheat-smuggle-final` | `cheat-smuggle__rUCFCDr` | 0.0000 |

The matching round-1 baselines are `annu-cheat1-before-retry`
(`annu-cheat1__D33RjNp`, 0.0), `annu-cheat2-before` (`annu-cheat2__nU37MTH`,
0.0052), `annu-cheat3-before` (`annu-cheat3__Yy9bdS9`, 0.0022) and
`cheat-smuggle-before` (`cheat-smuggle__bXvJfQa`, 0.8333).

### Verifying the gate itself

`proof/audit-probe.txt` calls the audit directly in `golang:1.23` against 27
synthetic workspaces plus the real oracle (28 assertions). The oracle must be
clean; the real solution's workspace is; every bypass must be rejected:
escaped/raw imports, aliased `os.StartProcess`, a hidden `_p` package,
`.syso`/`.s`, `//go:embed`, cgo, `go.work`, symlinks and the Python-binary
signature. All 28 assertions pass. `proof/cheats/cheat4/solve.sh` is the exact
smuggler that scored 0.8333 before this round.

## Changed files

- `task/tests/Dockerfile` — `golang:1.23`, `runner` user, interpreters and
  stdlib chmod 700.
- `task/tests/test.sh` — runs only the checks directory.
- `task/tests/checks/_common.py` — shared audit (files, symbols, `go list`
  import graph) and exam runner used by every criterion.
- `task/tests/checks/build.py` — build plus audit plus ≥ 0.98 exam gate.
- `task/tests/checks/no_python.py` — audit, runtime interpreter probe, exam gate.
- `task/tests/checks/behaviour.py` — audit, overall and edge-case floors, 0.10 factor.
- `task/tests/checks/reward.toml` — weights 1 / 1 / 4 over build / no_python / behaviour.
- `task/tests/data/inputs.txt`, `task/tests/data/answers.txt` — new 100,000-line exam.
- `task/solution/solve.sh` — real Go port, fixed against the new exam
  (`capFirst` underscore/digit handling, `\w.\w` inline periods, ASCII-only
  upper-later rule, Python leftmost-first small-word alternation).
- `task/instruction.md`, `task/task.toml` — chosen mode, rules and thresholds.
- `task/solution/solve.real.sh` — removed; it was a byte-identical duplicate of
  `solve.sh` at the previous commit.
- `kit/` — `make_pool.py`, `answers.py`, `compare.py`, `report.txt`, evidence of
  the old exam and old verifier.
- `proof/cheats/cheat4/solve.sh`, `proof/audit-probe.txt`,
  `proof/reattack-round2.txt` — round-2 evidence.
- `measure/`, `proof/`, `HARDEN.md`, `DEFENCE.md` — new.

## What I learned

1. A "no Python" rule enforced by file suffix is not a Python-free rule: the
   runtime image, not the repository, decides whether an interpreter exists.
   The check has to test the capability (can this process start an interpreter?)
   rather than the artefact (is there a `.py` file?).
2. Structural criteria are the soft spot. Any point awarded for "it compiles"
   or "the tree is clean" is free reward, so those points must be gated on the
   behaviour they are supposed to prove.
3. Linear partial credit plus a corpus where easy lines outnumber hard lines
   turns a weak port into a passing score. Floors plus an edge-heavy pool make
   the score track correctness instead of coverage.
