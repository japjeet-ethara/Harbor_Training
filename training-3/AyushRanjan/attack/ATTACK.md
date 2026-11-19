# Day 4 attack report — Akul Malviya

## Target and method

- Target: Akul Malviya, `AkulMalviya/titlecase-go`
- Source commit: `528c84e137b3740c4e710ace7fcbc1866b515d3d`
- Local target copy: `attack/target/` (ignored; never staged)
- Harbor agent: `oracle`
- Each final run used a fresh scratch copy and changed only `solution/solve.sh`.
- Akul's task writes one scalar reward to `verifier/reward.txt`; Harbor records it as `verifier_result.rewards.reward`. It does not emit separate build/no_python/behaviour values.

## Cheat 1 — Build-only empty program

**What it does:** Deletes the copied Python files and writes an empty Go `main` that builds. It makes no attempt to transform input.

**Score:** `0.0` (Harbor result JSON: `results/cheat1-reward.json`).

**Job:** `jobs/ayush-day4-cheat1-harbor/target__dpiN9rx` (trial `target__dpiN9rx`, result ID `99650c3b-51ff-4c6a-a2ee-3b36f47494c0`).

**Why:** The target's shell test requires `go build` at `tests/test.sh:17-21`, then runs the executable at `tests/test.sh:23-30` and scores output comparisons at `tests/test.sh:32-40`. Only the behaviour fraction is written as the reward at `tests/test.sh:44-53`, so compiling alone earns no points.

**Fix:** Keep the behaviour gate. This cheat did not pass it and received no partial reward.

## Cheat 2 — Read hidden answer files at runtime

**What it does:** Builds a small Go table lookup that opens `/tests/data/hidden_inputs.txt` and `/tests/data/hidden_expected.txt` at runtime, then prints the stored answer for each input. It is not a titlecase implementation.

**Score:** `0.0` in Harbor (`results/cheat2-reward.json`). The Go program's diagnostic output confirms it opened both files and matched all 2,000 input records, but the verifier still recorded no matching output lines because the committed expected file uses CRLF while the Go output uses LF.

**Job:** `jobs/ayush-day4-cheat2-harbor/target__z7bkDAs` (trial `target__z7bkDAs`, result ID `9946120d-8559-4781-ab69-a6a07914b433`).

**Why:** `tests/test.sh:44` gives the solution's process access to the same `/tests/data/hidden_inputs.txt` and `hidden_expected.txt` that the verifier reads. The expected file is therefore reachable from the candidate process. Separately, `tests/test.sh:32-40` compares raw lines; the committed expected file has CRLF endings, so the lookup's LF output is counted wrong. The data file's CRLF is present in the Git archive from the source commit, not introduced by editing the target.

**Fix:** Keep expected answers out of the filesystem visible to the candidate process; isolate the candidate execution from verifier data. Also normalize line endings consistently (or strip a trailing carriage return) before comparing so the score reflects behavior.

## Cheat 3 — Go wrapper calling Python

**What it does:** Builds a Go executable that delegates input to `python3 -c` and imports `titlecase`, without leaving any `.py` files in `/workspace/repo`.

**Score:** `0.0` (`results/cheat3-reward.json`). The verifier output records `ImportError: cannot import name 'titlecase' from 'titlecase' (unknown location)`.

**Job:** `jobs/ayush-day4-cheat3-harbor/target__SR2xsdM` (trial `target__SR2xsdM`, result ID `9e0ac7e2-06f2-4fdf-97b9-64514b612714`).

**Why:** The `.py` check only searches files under `/workspace/repo` at `tests/test.sh:9-12`; it does not prohibit invoking a Python interpreter. The attempted workaround failed in this image because the importable `titlecase` implementation was absent after the `.py` files were deleted. The task image is based on `golang:1.23` at `environment/Dockerfile:2`.

**Fix:** Keep the current Go-only environment and ensure no Python titlecase package is installed or reachable at runtime. The `.py`-file check alone is not a general proof that Python is not used.

## Evaluation issue found

The current Harbor numbers are the real results from the committed target copy, but they do not establish that the lookup cheat is ineffective: it read all hidden inputs and answers successfully. The committed expected file uses CRLF, while the lookup executable emits LF, and the evaluator compares `$0` exactly at `tests/test.sh:34`. This masks the lookup result as `0.0`. The line-ending issue must be corrected by the task owner before scores can reliably measure solution quality; I did not edit the target's tests or environment.

## Summary

- Highest measured Harbor score: `0.0`.
- Strongest confirmed exposure: runtime access to all 2,000 hidden input/answer pairs; the score is masked by the line-ending defect.
- Main hardening action: isolate expected answers from the candidate process and fix CRLF/LF comparison behavior.
