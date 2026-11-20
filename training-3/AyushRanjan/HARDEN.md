# Day 5 — Task Hardening Report

## 1. Executive Summary

I hardened Ayush Ranjan's Go titlecase task against the three supplied attacks from Nitin Ethara and verified the fixes in Harbor. The original task awarded a full behavior score when a candidate printed the verifier's answer file, and the test process ran the candidate with access to that file. The new evaluator uses a separate 100,000-input frozen exam, protects its expected answers, runs the candidate as an unprivileged user without Python execution access, and gives behavior credit only for exact complete output.

Final Harbor results on the hardened task: oracle **1.0**; Nitin Cheat 1 **0.0**; Cheat 2 **0.0**; Cheat 3 **0.0**. The 100K differential test found additional bugs in Ayush's Go port; those were fixed without changing the reference answers. Nitin's folder was not modified.

## 2. Attacker Analysis

| Attack | What it does | Original weakness |
|---|---|---|
| Cheat 1 | Reads `/tests/data/hidden_expected.txt` and prints it (`NitinEthara/attack/cheat1/solve.sh:21-28`). | The test image copied the answer file into `/tests/data/`, and the candidate executable ran in the same verifier container without privilege separation. `behaviour.py:20-26, 43-56` loaded that file and launched the candidate. |
| Cheat 2 | Implements only a small subset of titlecase rules (`cheat2/solve.sh:24-62`). | The behavior criterion granted fractional credit for line matches (`behaviour.py:68-75`), so incomplete behavior still earned a reward. |
| Cheat 3 | Runs embedded Python via `exec.Command("python3", "-c", code)` (`cheat3/solve.sh:21-40`). | `no_python.py:20-40` only searched the candidate repository for `.py` files. The verifier image included Python and the candidate shared its execution context. |

## 3. Baseline Results

Each supplied `solve.sh` was run alone in a fresh scratch copy of the original task with Harbor 0.25.0 and the `oracle` agent. Cheat 2's first attempt failed before verifier startup because Docker Hub returned an HTTP/HTTPS transport error; the successful retry below is the score used. Aggregate and per-component reward JSONs are saved in `measure/baseline/`.

| Attack | Original score | Behavior / build / no_python | Job folder |
|---|---:|---|---|
| Cheat 1 | 0.6667 | 1.0 / 0.0 / 0.0 | `jobs/ayush-day5-baseline-cheat1/ayush-day5-baseline-cheat1` |
| Cheat 2 | 0.0887 | 0.133 / 0.0 / 0.0 | `jobs/ayush-day5-baseline-cheat2-retry/ayush-day5-baseline-cheat2-retry` |
| Cheat 3 | 0.0887 | 0.133 / 0.0 / 0.0 | `jobs/ayush-day5-baseline-cheat3/ayush-day5-baseline-cheat3` |

Cheat 1's 0.6667 came entirely from printing the hidden expected outputs. Cheat 2 and Cheat 3 each received 0.133 behavior credit for partial matches.

## 4. Vulnerabilities and Fixes

### Cheat 1 — Answer-file lookup

- **Root cause:** the verifier copied `hidden_expected.txt` into `/tests/data/`, and the candidate process could read verifier files.
- **Changes:** replaced the old test data with `inputs.txt` and `answers.txt`; the verifier reads the answers as root, changes the answer file to mode `0400`, and launches the candidate as UID/GID 65534. The candidate receives only test inputs through stdin. The old answer filename no longer exists in the verifier image.
- **Why it works:** the supplied lookup script cannot find its old path. A candidate process running as UID 65534 also cannot read the root-owned `answers.txt` file.
- **Evidence:** final Harbor Cheat 1 reward is 0.0; component JSON is `measure/after/cheat1-details.json`.

### Cheat 2 — Incomplete titlecase implementation

- **Root cause:** the old criterion awarded a fractional score for matching lines from only 2,000 hidden inputs.
- **Changes:** behavior now compares the entire output line list to all 100,000 reference answers; any wrong line, missing line, extra line, or nonzero exit gets behavior score 0. The reward weights are build 0.5, no_python 0.5, behavior 9.0, so structural checks alone can contribute at most 0.1.
- **Why it works:** the partial program cannot gain a behavior fraction from common cases or match-count arithmetic. The larger dataset also covers many more edge combinations.
- **Evidence:** final Harbor Cheat 2 reward is 0.0; component JSON is `measure/after/cheat2-details.json`.

### Cheat 3 — Python launched from Go

- **Root cause:** the old `.py` scan did not restrict subprocess execution, and Python was installed in the verifier image.
- **Changes:** the candidate runs as UID/GID 65534 with a restricted `PATH` that omits `/usr/local/bin`; the verifier Dockerfile also changes `/usr/local/bin/python3.12` to mode `0700`. The verifier itself runs as root, so its Python-based test runner remains usable.
- **Why it works:** Nitin's exact script resolves `python3` by name and cannot find it. The interpreter executable is also not executable by the unprivileged candidate even if it tries the usual absolute executable path.
- **Evidence:** final Harbor Cheat 3 reward is 0.0; component JSON is `measure/after/cheat3-details.json`.

### Oracle corrections found by the 100K exam

The stricter exam initially found 11,860 mismatches in the Go port. I fixed the port's Python-compatible handling for ASCII-only `UC_ELSEWHERE` matching, Unicode `\w` in inline-period checks, apostrophe suffixes, punctuation prefixes, small-word boundaries inside slash forms, subphrase regex ordering, and optional punctuation after terminal small words. I kept all generated inputs and reference answers unchanged. The provided comparison script then reported **0 wrong answers out of 100,000**.

## 5. After-Hardening Results

These are final Harbor reruns after the verifier image and scoring changes. Aggregate and component JSONs are saved in `measure/after/`.

| Attack | Before | After | Final job folder |
|---|---:|---:|---|
| Cheat 1 | 0.6667 | 0.0 | `jobs/ayush-day5-verified-cheat1/ayush-day5-verified-cheat1` |
| Cheat 2 | 0.0887 | 0.0 | `jobs/ayush-day5-verified-cheat2/ayush-day5-verified-cheat2` |
| Cheat 3 | 0.0887 | 0.0 | `jobs/ayush-day5-verified-cheat3/ayush-day5-verified-cheat3` |

Oracle: **1.0**, with behavior 1.0, build 1.0, and no_python 1.0. Final job folder: `jobs/ayush-day5-verified-oracle/ayush-day5-verified-oracle`.

## 6. Dataset Improvement

- Original behavior exam: 2,000 hidden inputs. All 2,000 original hidden cases remain active as a protected regression check in `task/tests/data/legacy-2k/`; the original visible/hidden pairs are also preserved in ignored `kit/old-2k/` for measurements.
- New pool: 100,000 unique inputs, seed 1, generated with the trainer's `make_pool.py`.
- Reference mode: **without the optional `regex` module**. The bundled titlecase source reports `REGEX_AVAILABLE=False`, so it uses the standard-library `re` fallback. This mode is stated in `task/instruction.md`.
- Double execution: trainer `answers.py` ran the original reference twice with `PYTHONHASHSEED=1` and `2` and kept only equal outputs.
- Stability: 100,000 retained, 0 discarded as unstable.
- Main exam files: `task/tests/data/inputs.txt` and `task/tests/data/answers.txt`; 100,000 lines in each, valid UTF-8, final newline, no missing records. Input records are unique. Repeated answer strings are expected when different inputs produce the same output. Behavior also checks the preserved 2,000 hidden legacy records, for 102,000 exact records total.
- Determinism: a second pool generation produced byte-identical inputs (SHA-256 `132bdd057a2ac492ef89c74b92177049b0eac76686eee0373c9a88e765ac7dc2`). Frozen answer SHA-256: `3d46633407b6424c9fd62cbe7c147515154f3a9395cc1577078b08642b4faf3d`.
- Generation and validation evidence: `measure/generation-report.txt`. The trainer scripts are in `kit/`; only the Windows UTF-8 stdout setup was added to the local working copies of `answers.py` and `compare.py`.

## 7. Three-Port Comparison

All ports ran as line-oriented executables in a Go 1.23 Linux container. The two classmate implementations are copied verbatim into ignored `ports/`; wrappers only compile/run them. No classmate source files were changed.

| Port | Wrong answers / 100K | Old 2K caught errors? | Probability a random 2K misses all observed 100K errors |
|---|---:|---|---:|
| Ayush Ranjan (oracle) | 0 / 100,000 | No (0 errors) | 100% (no errors observed) |
| Aahan Trikha | 3,900 / 100,000 | No (0 errors) | approximately `1.2291e-35` |
| Charitra | 0 / 100,000 | No (0 errors) | 100% (no errors observed) |

There were no crashes or output-count mismatches for these runs. Aahan's actual old 2K run passed all 2,000 inputs despite its 3,900 errors on the new exam. Detailed reproducible reports, including trainer `compare.py` output, are in `measure/my-oracle.txt`, `measure/AahanTrikha.txt`, and `measure/Charitra.txt`.

## 8. Lessons Learned

1. A test file is not hidden merely because the instruction calls it hidden. If the candidate process can read its path, it can return the answers instead of implementing the behavior.
2. Exact whole-output checks and line-count checks close easy partial-credit shortcuts. A passing build is useful evidence, but it does not demonstrate the program works.
3. A small random exam can miss systematic edge-case failures. Aahan's port passed all 2,000 old hidden inputs but had 3,900 wrong answers in 100,000 cases.

## 9. Remaining Limitations

- These results demonstrate resistance to Nitin's three supplied scripts and the measured ports; they do not prove universal security against every possible malicious Go program.
- The 100K exam is finite. Unseen inputs may still reveal differences outside this distribution.
- The no_python criterion still checks filenames in the submitted repository. The execution boundary blocks ordinary Python invocation by the candidate; it is not a general sandbox against arbitrary native code or a separately bundled interpreter.
- The Day 6 empty-solution (`nop`) score and proof bundle have not been run as part of Day 5.
