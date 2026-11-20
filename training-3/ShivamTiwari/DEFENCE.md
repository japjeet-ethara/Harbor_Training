# Defence — five-minute technical walkthrough

## 1. Strongest original cheat and its score

The strongest cheat in the Day 4 report was **Cheat 1, "Python inside"**: it
scored **1.0** — full marks on build, no-Python and behaviour. It is the one
that matters, because it did not approximate the task at all; it ran the
original Python function and let the Go program be a launcher.

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

- **Runtime:** the verifier image is now `golang:1.23`. It creates an
  unprivileged `runner` user and runs `chmod 700 /usr/bin/python*` and
  `/usr/local/bin/python*`. The submitted binary is executed as `runner` from
  `/tmp`.
- **Capability probe:** `no_python` actively tries to start `python3` as
  `runner`; if that succeeds, the check fails.
- **Static scan:** `no_python` rejects Python suffixes, embedded Python source
  markers, interpreter-binary markers, `//go:embed`, cgo, `os/exec`, `syscall`,
  `plugin`, `unsafe`, `os.StartProcess`, `exec.Command`, and `require` lines in
  `go.mod`.
- **Correctness gate:** `build` and `no_python` require ≥ 98% exam accuracy, so
  neither can be earned by a stub.
- **Behaviour gate:** `behaviour` keeps fractional credit but requires ≥ 98%
  overall and ≥ 95% on edge cases; below either floor the value is multiplied
  by 0.10.
- **Exam:** 100,000 unique seeded inputs, reference mode `re`
  (`REGEX_AVAILABLE = False`), answers frozen from the Python implementation run
  twice per line (0 dropped), and zero overlap with public examples.

## 5. Before and after

| Cheat | Before (report) | Now (rerun) |
|---|---|---|
| Python inside | 1.0000 | 0.0000 |
| Half port | 0.4530 | 0.0036 |
| Delete + NOTES lookup | 0.3883 | 0.0022 |

The reruns are real Harbor jobs (`harden-runs/jobs/cheatN-hardened`). The cheat
scripts are reconstructions of the reported mechanisms because the attacker's
original job folders were not available in this workspace.

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
- The static Go scan can be evaded in principle by building forbidden import
  paths at runtime, but the capability probe and the file permissions make an
  escape useless: there is no interpreter for `runner` to reach.
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
