# measure: port comparison and corrected-oracle results (Day 5, 2026-11-19)

This folder holds the three-port comparison on the round-1 and round-2 exams, the corrected task
oracle (a separate result), and the round-2 Harbor rewards. The exam itself, and the tools that
generated it, are in `../kit/`.

## Exams

| Exam | Files | Records | SHA-256 (inputs / answers) |
| --- | --- | ---: | --- |
| Round 1, no longer graded | `../kit/evidence/old-exam-2000/hidden_inputs.txt`, `hidden_expected.txt` | 2,000 | `017c6ffc7992c0df12185961d24d4ca6266432eebb406c18bcf25e941664e852` / `4dcc8d7b9f0a866fb209de6ba171be07dfe30030d595959315cf1118af1daf9a` |
| Round 2, graded | `../task/tests/data/inputs.txt`, `answers.txt` | 100,000 | `779b81d3930a23b0f3af5cf56ef19de29dea3cb632e6aca1fce2a5e20da9606f` / `e583966925128443d0fc96d605bed9b486c72463e14b79f66a1add0343ac1b36` |
| Practice, not graded | `../task/tests/data/practice_inputs.txt`, `practice_expected.txt` | 2,000 | `2f086c791fa087200506e0a6eba7dd58517884d5b98ac63dc07e89e62f269052` / `04afbf845881398322c49da41c8ca658436a5c337ef96a69356d8df3b90232f2` |

`../kit/compare.py` expects `<suite>/inputs.txt` and `<suite>/answers.txt`. For the round-1 and
practice exams, a suite folder held byte copies under those names, checked by hash.

## Solutions measured

| Port | Owner | Source path (repo) | Commit (last change) | `solve.sh` git blob |
| --- | --- | --- | --- | --- |
| Task oracle (original) | Pragati Sharma | `training-3/PragatiSharma/task/solution/solve.sh` | `6504b045a6c358671884ca981b6862e0cc9f0031` | `d33fd17c34bbb858c769269e7f692c9ae8a0f840` |
| Classmate 1 | Ayush Khurana | `training-3/AyushKhurana/task/solution/solve.sh` | `9234582e9622646649126693222a084ac139dad5` | `631b59c3560cd559d042daf8710bfd168b952ddf` |
| Classmate 2 | Priyanshu Singh | `PriyanshuSingh/titlecase-go/solution/solve.sh` | `30cf18a169cd98968abf78f95c091e123983890b` | `18a11760627dd95b3a4671dbe130adc3f4df7ed8` |

Repository HEAD at measurement time was `cfa79805bd953a91f385b1b749c36ae8e0e38db9`, and all
three files were identical there. Priyanshu Singh's solution is also identical at
`ef58d2a95f5a6b3ee782d878b7bdb6c19088cbac`, the commit pinned in this folder's attack review.

Why these two: Ayush Khurana attacked this task, and this task's attack targeted Priyanshu
Singh's. Both oracles were read in full before running. Both are standard-library Go ports
with no `os/exec`, no Python, no network and no embedded answers.

## Environment and commands

- Go: `golang@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0`
  (go1.23.12), `GOTOOLCHAIN=local`.
- Python: `ghcr.io/astral-sh/uv@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1`,
  uv 0.9.30, Python 3.14.2, `UV_PYTHON_DOWNLOADS=never`; always `python -I`.
- Host: Docker Desktop (WSL 2) on Windows 11. Runtimes are a single run, timing the program
  alone (bash `time` inside the container).

Each solution was exported with `git -c core.autocrlf=false archive <commit> <solution dir>
<environment dir>`, and the blob ids were checked. Then:

```sh
GO=golang@sha256:60deed95d3888cc5e4d9ff8a10c54e5edc008c6ae3fba6187be6fb592e19e8c0
UV=ghcr.io/astral-sh/uv@sha256:7cf77f594be8042dab6daa9fe326f90962252268b4f120a7f5dccce4d947e6c1

# Build: the task's environment repo is copied inside the container, solve.sh runs, then the
# grader's commands (go build ./..., go build -o titlecase .). Network off.
docker run --rm --network none -e GOTOOLCHAIN=local \
  -v <task>/environment/repo:/env:ro -v <task>/solution:/sol:ro \
  -v measure/tools:/tools:ro -v <build>:/out $GO bash /tools/build_port.sh <sh|bash>

# Run: network off, read-only root, unprivileged user, 2 GB memory.
docker run --rm --network none --read-only --tmpfs /tmp --user 65534:65534 --memory 2g \
  -v <build>/titlecase:/port/titlecase:ro -v <suite>:/suite:ro \
  -v measure/tools:/tools:ro -v <run>:/out $GO bash /tools/run_port.sh

# Score: trainer's compare.py as documented, then a byte-level cross-check (LF-only records).
docker run --rm --network none --read-only --tmpfs /tmp --tmpfs /root \
  -e UV_PYTHON_DOWNLOADS=never -e UV_CACHE_DIR=/tmp/uvc \
  -v kit:/kit:ro -v measure/tools:/tools:ro -v <suite>:/suite:ro -v <run>:/run:ro $UV \
  sh -c 'uv run --no-project --python 3.14 python -I /kit/compare.py /suite /run/got.txt;
         uv run --no-project --python 3.14 python -I -B /tools/score_bytes.py /suite /run/got.txt'

# Mismatch analysis for a failing port:
uv run --no-project --python 3.14 python -I -B measure/tools/mismatch.py \
  <suite> <run>/got.txt <out.tsv> kit/tools/families.py
```

`run_port.sh` writes `got.txt`, `stderr.txt`, `exit.txt` and `time.txt` (real, user and sys
seconds). Per the SOP, `got.txt`, the binaries and the run folders are not committed.

## Results: the original three ports (baseline, before any fix)

| Port | Exam | Correct | Incorrect | Output lines / expected | Exit | Runtime real / user / sys (s) |
| --- | --- | ---: | ---: | --- | ---: | --- |
| Task oracle (original) | round 1, 2,000 | 2,000 | 0 | 2,000 / 2,000 | 0 | 0.051 / 0.006 / 0.014 |
| Task oracle (original) | round 2, 100,000 | 96,937 | **3,063** | 100,000 / 100,000 | 0 | 1.516 / 0.816 / 0.099 |
| Ayush Khurana | round 1, 2,000 | 2,000 | 0 | 2,000 / 2,000 | 0 | 0.064 / 0.023 / 0.010 |
| Ayush Khurana | round 2, 100,000 | 100,000 | 0 | 100,000 / 100,000 | 0 | 2.388 / 1.522 / 0.124 |
| Priyanshu Singh | round 1, 2,000 | 2,000 | 0 | 2,000 / 2,000 | 0 | 0.050 / 0.014 / 0.005 |
| Priyanshu Singh | round 2, 100,000 | 100,000 | 0 | 100,000 / 100,000 | 0 | 1.546 / 0.687 / 0.141 |

- No run wrote to stderr, and no output contained a CR.
- Both classmates' round-2 outputs are byte-identical to `answers.txt`, and all three round-1
  outputs are byte-identical to `hidden_expected.txt`.
- compare.py estimates a 0% chance that a random 2,000-title suite would miss all 3,063
  failures. The round-1 exam contained none of the triggering characters.

The original oracle's failures (`oracle/baseline-mismatch-causes.txt`) all come from Go's
one-to-one case mapping:

| Lines | Cause |
| ---: | --- |
| 1,329 | `ﬂ` first in a word; Python's `upper()` gives `FL`, Go keeps `ﬂ` |
| 1,305 | `ﬁ` first in a word; Python's `upper()` gives `FI`, Go keeps `ﬁ` |
| 19 | both ligatures |
| 410 | `İ` in an all-caps line or all-caps hyphen/slash part: Python's `lower()` gives `i` + U+0307, Go gives `i` |

## Results: corrected task oracle (separate result)

| Version | `solve.sh` SHA-256 | Round 1, 2,000 | Round 2, 100,000 | Practice, 2,000 | Regression titles (74) |
| --- | --- | --- | --- | --- | --- |
| Original | `91c5db4ce06cd206dff6dfb7485759520ff4b4c8e0fda5d14b8b3088b8ddb89e` | 2,000 | 96,937 | 2,000 | 22 |
| Fix 1: full case mappings | `febcb4a48225b2933d24334ddccb986e5e3a31ac4c1a5368391dc7516207f6a1` | 2,000 | 100,000 | 2,000 | 61 |
| Fix 2 (final, now `../task/solution/solve.sh`) | `8546e114cf5e717f09f07d94c64ed31123edfb343fcc6d18316fc768fa69c0e8` | **2,000** | **100,000** | **2,000** | **74** |

- **Final version runs:** every run exited 0 with no stderr and one LF-terminated line per
  input.
  - Runtime real / user / sys (s): round 1 0.048 / 0.018 / 0.004; round 2
    1.872 / 1.021 / 0.102; practice 0.051 / 0.009 / 0.013.
  - Its round-2 output is byte-identical to `answers.txt`.
- **Fix 1 runs:** round 1 0.047 s, round 2 1.636 s.

What the final version adds is all generated from Python 3.14.2 (Unicode 16.0.0) on top of Go's
Unicode 15.0.0 tables:

- `str.upper()`, `str.lower()` (with Final_Sigma) and `str.capitalize()`: 129, 28 and 75
  mapping exceptions, plus 96 Case_Ignorable/Cased exceptions (`pycase.go`,
  `pycase_tables.go`).
- `\w`: 5,004 code points added (Unicode 16.0 letters and digits). `\s`: U+001C to U+001F
  added (`pyregex.go`, `pyregex_tables.go`).
- `re.IGNORECASE` folding to ASCII letters: `İ`/`ı` to `i`, `ſ` to `s`, Kelvin sign to `k`.
  Used for small words, honorifics, consonant acronyms and the apostrophe rule.

### Oracle checks and commands

| Check | Result |
| --- | --- |
| Build offline (go1.23.12), `gofmt -l`, `go vet` | ok, clean, ok |
| Imports | `bufio fmt os strings unicode unicode/utf8` |
| Casing helpers vs Python, every code point (1,112,064) × 4 properties | 0 mismatches |
| `\w`, `\s`, IGNORECASE fold vs Python's `re`, every code point | 0 mismatches |
| 32,500 casing strings (every `xΣy` context plus random) × 3 functions | 0 mismatches |
| Negative controls: delete the `İ`/`ﬁ` table entries; delete the `ı` fold and U+001C to U+001F | tests fail and name those code points |
| Regression titles (`oracle/regression/`), byte for byte, mismatches shown as code points | original 22/74, fix 1 61/74, final 74/74 |

```sh
# Tables: Go facts, then Python facts -> generated Go source (then gofmt).
go run measure/oracle/tools/godump.go > go-unicode-dump.tsv            # in $GO, offline
go run measure/oracle/tools/godump_classes.go > go-classes-dump.tsv    # in $GO, offline
uv run --no-project --python 3.14 python -I -B measure/oracle/tools/mkcasing.py go-unicode-dump.tsv pycase_tables.go casing-ref.tsv
uv run --no-project --python 3.14 python -I -B measure/oracle/tools/mkclasses.py go-classes-dump.tsv pyregex_tables.go classes-ref.tsv
uv run --no-project --python 3.14 python -I -B measure/oracle/tools/mkhelpercases.py helper-cases.tsv
# Exhaustive helper tests: copy the built sources plus helpers_test.go into a scratch module.
CASING_REF=casing-ref.tsv HELPER_CASES=helper-cases.tsv CLASSES_REF=classes-ref.tsv go test -count=1 -v ./...
# Regression titles: inputs, then answers frozen twice from the pinned original, then check.
uv run --no-project --python 3.14 python -I -B measure/oracle/tools/make_regression_cases_r2.py pool.txt labels.tsv
uv run --no-project --python 3.14 python -I kit/answers.py <python-titlecase@42f43e2> pool.txt suite
uv run --no-project --python 3.14 python -I -B measure/oracle/tools/check_regression.py suite labels.tsv <run>/got.txt
```

The generated reference files (`*-dump.tsv`, `*-ref.tsv`, `helper-cases.tsv`) are regenerable
and not committed.

## Harbor results, round 2 (100,000 inputs)

Harbor 0.25.0. Each run used a fresh copy of the candidate task with only
`solution/solve.sh` replaced: `harbor run -p <copy>/task -a oracle`, or `-a nop`. The reward
files are in `harbor/`. Job folders are local and not committed; `../HARDEN.md` lists their
paths.

| Run | build | no_python | behaviour (matches) | reward |
| --- | --- | --- | --- | --- |
| Corrected oracle | 1.0 | 1.0 | 1.0 (100000/100000) | **1.0** |
| Nop | 0.0 | 0.0 | 0.0 (failed build condition) | **0.0** |
| Cheat 1 (Ayush, unchanged) | 1.0 | 1.0 | 0.0205 (2046/100000) | **0.0205** |
| Cheat 2 (Ayush, unchanged) | 1.0 | 1.0 | 0.0 (exit 1, `no python found`) | **0.0** |
| Cheat 3 (Ayush, unchanged) | 1.0 | 1.0 | 0.0204 (2045/100000) | **0.0204** |
| Task cheat (`cheat/solve.sh`) | 1.0 | 0.0 | 0.0 (3 `.py` files remain) | **0.0** |

There were no exceptions and no errored trials.

## Evidence

| Committed here | Content |
| --- | --- |
| `oracle/baseline-mismatch-causes.txt` | The original oracle's 3,063 failures, by cause and word family |
| `oracle/regression/` | 74 regression inputs, labels, answers and `answers.py` report |
| `oracle/tools/` | Table generators, exhaustive helper tests, negative controls, regression tools |
| `tools/` | `build_port.sh`, `run_port.sh`, `score_bytes.py`, `mismatch.py` |
| `harbor/` | `reward.json` for each round-2 Harbor run, plus `runs.tsv` (job and trial ids) |
| `../kit/evidence/old-exam-2000/` | The round-1 exam used above |

Local only, not committed (the SOP excludes outputs, binaries and jobs). Paths are under
`C:\Users\PragatiSharma\Documents\harbor-work\day5-tests\exam100k\`:
- `runs\BASELINE.md`, `runs\`, `ports\`: the baseline runs, binaries and source exports, with
  `logs\baseline-manifest.sha256`;
- `oracle-fix\REPORT.md`, `oracle-fix\REPORT-r2.md`, `oracle-fix\runs-r2\`, `oracle-fix\logs\`:
  the corrected-oracle runs and logs;
- `hv\jobs\`, `hv\evidence\`: the full Harbor jobs and verifier logs.
