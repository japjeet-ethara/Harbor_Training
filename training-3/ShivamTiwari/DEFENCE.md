# Defence — five-minute technical walkthrough

## 1. Strongest original cheat and its score

The strongest cheat in the Day 4 report was **Cheat 1, "Python inside"**: it
scored **1.0** — full marks on build, no-Python and behaviour. It is the one
that matters, because it did not approximate the task at all; it ran the
original Python function and let the Go program be a launcher.

The strongest *residual* cheat found while preparing for the re-attack was
worth **0.8333** against the round-1 task: copy `/usr/bin/python3.11` into the
repository and run the copy. The round-1 scan lived only inside `no_python`,
`build` and `behaviour` never looked at structure, and the stdlib was still
readable, so perfect behaviour plus the build point survived. The shared gate
in section 4 closes it; the score is 0.0000 now.

## 2. How the cheat worked

1. Copy `titlecase/__init__.py` to a plain text file, `py_engine.txt`.
2. Delete every `.py` file so a filename check sees a clean repository.
3. Compile a Go program that embeds the Python source with `//go:embed`.
4. At runtime, write the embedded source to a temp file and pipe stdin through
   `/usr/local/bin/python3 -c`.
5. The output is then byte-identical to the reference by construction, so the
   behaviour check and both structural checks all pass.

## 3. Why the original verifier allowed it

Two independent mistakes lined up:

- `tests/no_python.py` asked a **filename** question (`name.endswith(".py")`)
  instead of a **capability** question. The Python source was still in the
  workspace, just renamed.
- `tests/Dockerfile` inherited from `python:3.12-slim`, so `/usr/local/bin/python3`
  was present and executable in the very image that ran the submitted binary.
  Nothing in the verifier tried to start an interpreter, so nothing noticed.

The other two cheats exploited the scoring model rather than an execution
escape: build and no_python paid out for compiling and for deleting files, and
behaviour paid linear partial credit on a corpus where easy words outweighed
edge cases.

## 4. Exact hardening change

- **Shared gate:** `tests/checks/_common.py` owns `audit()` and `exam()`.
  `build`, `no_python` and `behaviour` all call them, so a structural
  violation scores 0 on every criterion instead of keeping 5 of 6 points.
- **Runtime:** the verifier image is now `golang:1.23`. It creates an
  unprivileged `runner` user and runs `chmod 700 /usr/bin/python*`,
  `/usr/local/bin/python*`, `/usr/lib/python3*`, `/usr/local/lib/python3*` and
  `libpython*`. The submitted binary is executed as `runner` from `/tmp`.
- **Capability probe:** `no_python` actively tries to start `python3` as
  `runner`; if that succeeds, the check fails.
- **Static scan + import graph:** the audit rejects Python suffixes, embedded
  Python source markers, interpreter-binary markers, `//go:embed`, cgo,
  `StartProcess`, `exec.Cmd`, `syscall.Syscall`, and `require`/`replace`/
  `toolchain` lines. It then resolves the real module graph with
  `go list -deps`, so raw-string, escaped and aliased imports cannot hide
  `os/exec`, `syscall`, `plugin`, `unsafe`, `net*` or `golang.org/x/sys`.
- **Correctness gate:** `build` and `no_python` require ≥ 98% exam accuracy, so
  neither can be earned by a stub.
- **Behaviour gate:** `behaviour` keeps fractional credit but requires ≥ 98%
  overall and ≥ 95% on edge cases; below either floor the value is multiplied
  by 0.10.
- **Exam:** 100,000 unique seeded inputs, reference mode `re`
  (`REGEX_AVAILABLE = False`), answers frozen from the Python implementation run
  twice per line (0 dropped), and zero overlap with public examples.

## 5. Before and after

| Cheat | Before (report) | Round 1 (rerun) | Round 2 (final) |
|---|---|---|---|
| Python inside | 1.0000 | 0.0000 | 0.0000 |
| Half port | 0.4530 | 0.0036 | 0.0052 |
| Delete + NOTES lookup | 0.3883 | 0.0022 | 0.0022 |
| Copied interpreter (`cheat4`) | — | 0.8333 | 0.0000 |

The reruns are real Harbor jobs (`harden-runs/jobs/*-hardened` and
`harden-runs/jobs/*-final`). Round-2 trials: oracle `task__EtFCBdB`, nop
`task__eKGotkQ`, cheat1 `annu-cheat1__SNZh2na`, cheat2 `annu-cheat2__cHxeAgH`,
cheat3 `annu-cheat3__TZ2rt6e`, cheat4 `cheat-smuggle__rUCFCDr`. The three
original cheat scripts are reconstructions for round 1 and were re-run from
Annu Kumari's own `attack/cheatN/solve.sh` for round 2; the copied-interpreter
attack is my own (`proof/cheats/cheat4/solve.sh`) because it is the residual
hole round 1 left open. The half-port's small non-zero score is the below-floor
10% behaviour credit; its `build` and `no_python` are both 0.

## 6. Oracle and do-nothing validation

- Oracle (`harbor run -p task -a oracle`): **1.0** — behaviour 1.0, build 1.0,
  no_python 1.0, 100,000 of 100,000 lines exact. This also proves the real Go
  port compiles and runs in the Python-free verifier image.
- Do nothing (`harbor run -p task -a nop`): **0.0** — all three components zero.

## 7. Remaining limitations

- The behaviour score has a cliff at 98% / 95%. That is deliberate (it stops
  partial ports from banking most of the reward) but it is coarse: a port at
  97.9% loses most of its behaviour credit.
- The exam is deterministic. If the pool ever leaks into an agent image, a
  lookup table would work; today the pool is only in `task/tests/data/`, which
  is not part of the environment image, and regenerated copies in `kit/out/` are
  git-ignored.
- The audit resolves imports with `go list`, so raw-string, escaped and aliased
  spellings do not hide them, and packages skipped by the `./...` wildcard are
  still inspected because they are reachable. What remains outside the audit's
  view is a hand-written pure-Go reimplementation of the Python interpreter or
  of the titlecase transform; that is not a shortcut, it is the task.
- Below the 98% floor, behaviour still pays 10% of raw accuracy, so a half port
  earns about 0.5%. That is a deliberate gradient for near-misses, not a
  passing score: `build` and `no_python` are 0 below the floor.
- `unsafe` and `plugin` are banned because a straightforward port does not need
  them; an exotic legitimate implementation that did need them would be
  rejected.
- Cheat 2 and Cheat 3 are reconstructions, so their absolute scores are not the
  attacker's numbers — the before/after gap, not the exact digits, is the
  evidence.

## 8. Why the new exam is more reliable

- It is 50× larger and every line is unique, so a handful of memorised examples
  moves the score by 0.02% instead of several percent.
- 98.63% of lines are edge cases, so a port that only handles plain words
  cannot ride easy inputs to a passing score.
- Public examples were tested for exact overlap: 0 of 22 `NOTES.md` inputs and
  0 of 73 `TEST_DATA` inputs appear in the pool.
- The reference mode is pinned and documented (`re`, no optional `regex`
  package), and the Go oracle matches all 100,000 lines, so the exam measures
  the port rather than environment drift.
