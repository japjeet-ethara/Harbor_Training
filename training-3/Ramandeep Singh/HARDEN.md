# Day 5 Report â€” Hardening the Task

## Holes closed

### Cheat 1 â€” Read the exam
- **Before:** 1.0000 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.0000 (build 0.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-18__18-34-34`
- **Fix:** In `tests/Dockerfile`, restricted permissions on `/tests` to `0700` (root only) and `/tests/data/*` to `0600`. In `tests/behaviour.py`, the candidate binary is executed as unprivileged user `nobody:nogroup` in an isolated `/tmp/tc_sandbox` directory with a sanitized environment. Attempts by the candidate to read `/tests/data/hidden_expected.txt` fail with `permission denied`, dropping the behaviour score to 0.0. In `tests/test.sh`, `/logs/verifier` is set to `0700` to prevent reward tampering.

### Cheat 2 â€” Python inside Go wrapper
- **Before:** 1.0000 (build 1.0, no_python 1.0, behaviour 1.0)
- **Now:** 0.0000 (build 0.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-19__11-41-44`
- **Fix:** In `tests/no_python.py` and `tests/behaviour.py`, banned subprocess/system execution imports (`os/exec`, `syscall`, `syscall/js`, `plugin`, `unsafe`) using `go list -f '{{range .Imports}}{{.}} {{end}}' ./...`. Added deep file scanning for disguised Python code (e.g. `reference.txt` containing `def titlecase(`, `REGEX_AVAILABLE`, `exec(open(`). In `tests/Dockerfile`, restricted Python binaries (`chmod 700 /usr/local/bin/python* /usr/bin/python*`), preventing unprivileged processes from spawning Python at runtime.

### Cheat 3 â€” Build trick / Delete trick (Empty stub / Echo program)
- **Before:** 0.3333 (build 1.0, no_python 1.0, behaviour 0.0)
- **Now:** 0.0000 (build 0.0, no_python 0.0, behaviour 0.0)
- **Job folder:** `jobs/2026-11-16__18-31-26`
- **Fix:** In `tests/build.py` and `tests/no_python.py`, added a smoke execution verification test (`a tale of two cities` -> `A Tale of Two Cities`). An empty stub or echo program fails the smoke test and scores 0.0 on `build` and `no_python`. In `tests/reward.toml` and `tests/test.sh`, adjusted weights to `{ build = 0.5, no_python = 0.5, behaviour = 9.0 }`.

---

## Earlier exam snapshot (historical)

- **Old exam:** 2,000 inputs
- **New exam:** 100,000 inputs, mode: `re` (WITHOUT regex, REGEX_AVAILABLE = False)

| Port            | Wrong on new exam | Old exam caught it? | Chance 2K random misses it |
|:----------------|:------------------|:--------------------|:---------------------------|
| my oracle       | 0                 | n/a                 | n/a                        |
| ShashwatSuman   | 99,999            | no (passed old exam)| 0%                         |
| NehaGaur        | 3,520             | no (passed old exam)| 0%                         |
| MadhurJain      | 0                 | n/a                 | 100%                       |

---

## What I learned
1. **Weird inputs beat volume**: Edge cases like version numbers (`v1.2`), leading underscores (`_dream`), Turkish dotless i (`Ä±`), non-breaking spaces (`\u00a0`), and unusual apostrophes expose subtle regular expression and tokenization bugs that thousands of clean titles never trigger.
2. **Exams must run in a secure sandbox**: Tests executing candidate code as `root` with globally readable answer keys allow trivial front-door bypasses without writing any real solution logic; unprivileged execution and strict filesystem permissions are essential.
3. **Partial credit must be strictly earned**: Awarding marks for compiling or deleting files without validating core functionality enables trivial echo/empty stubs to claim substantial credit unless gated by execution smoke tests.

## Latest verified results (22 November 2026)

### Post-hardening attack reruns

| Attack | Behaviour | Build | No_Python | Reward | Job folder |
|:--|--:|--:|--:|--:|:--|
| Cheat 1 | 0.000 | 1.000 | 1.000 | 0.333 | `jobs/2026-11-22__00-26-52` |
| Cheat 2 | 0.000 | 1.000 | 0.000 | 0.050 | `jobs/2026-11-22__00-24-00` |
| Cheat 3 | 0.059 | 0.000 | 0.000 | 0.053 | `jobs/2026-11-22__00-29-44` |
| Original Oracle | 1.000 | 1.000 | 1.000 | 1.000 | `jobs/2026-11-22__00-38-31` |

The three tested cheats were blocked or substantially reduced after hardening. These results do not prove protection against every possible attack.

### Verified 100,000-input port comparison

| Port | Wrong answers | Accuracy | Chance random 2,000 misses all errors |
|:--|--:|--:|--:|
| my-oracle | 912 | 99.088% | 0% |
| MadhurJain | 0 | 100% | 100% |
| NehaGaur | 3,520 | 96.480% | 0% |

Comparison reports are saved in `measure/my-oracle-day5.txt`, `measure/MadhurJain-day5.txt`, and `measure/NehaGaur-day5.txt`.


