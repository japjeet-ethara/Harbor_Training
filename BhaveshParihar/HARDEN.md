# Day 5 Hardening Report

## 1. Task overview

This task is a Go implementation of Python `titlecase()`. The program reads
titles from standard input and writes titlecased titles to standard output.

The hidden examination checks that the implementation preserves the reference
library's behavior across titlecase rules and varied inputs. Its purpose is to
evaluate behavior beyond the visible examples, including interactions among
rules and punctuation, spacing, and Unicode cases.

## 2. Original security weaknesses

The following results are historical results from the supplied `ATTACK.md`
report. They are not measurements of the current hardened task and were not
independently reproduced for this report.

| Attack | Description | Historical reward |
|---|---|---:|
| Cheat 1 | Delete Python files without implementing titlecase behavior. | 0.0000 |
| Cheat 2 | Partial Go port that omitted important titlecase rules. | 0.2777 |
| Cheat 3 | Runtime search for hidden expected-answer files. | 0.3333 |

The supplied report lists historical job folders
`jobs/2026-11-19__17-55-50`, `jobs/2026-11-19__17-15-24`, and
`jobs/2026-11-19__18-14-41`, respectively. Those job folders and the referenced
reward files were not available for independent verification during this
documentation stage.

## 3. Stage A — Reward hardening

The overall reward in `tests/reward.toml` uses `weighted-sum`. Only `behaviour`
has a nonzero weight; `build` and `no_python` have weight zero in the overall
reward. Their component reports remain available independently.

Consequently, build success or passing the no-Python check cannot compensate
for incorrect behavior. A candidate with behavior score zero receives overall
reward zero.

## 4. Stage B — Examination hardening

The original hidden examination contains 2,000 cases. A deterministic
generator, `tests/strong_gen.py`, adds 2,400 strong hidden cases using seed
`20261121`. The resulting examination contains 4,400 hidden cases; the original
2,000 visible cases remain separate.

The strong input and reference-answer fixtures are:

- `tests/data/strong_hidden_inputs.txt`
- `tests/data/strong_hidden_expected.txt`

The strong expected answers are generated with the original Python
`titlecase()` reference implementation. The behavior verifier combines the
original and strong hidden inputs and expected answers, requires 4,400 output
lines, and compares each output with the expected line at the same position.
The score is the fraction of exact positional matches.

## 5. Stage C — Security audit

`task.toml` sets `environment_mode = "separate"`, so the candidate environment
and verifier environment are separate. The verifier sends hidden inputs to
the candidate through standard input; no candidate-accessible path to the
expected-answer files was confirmed during the audit.

The expected-answer fixtures are nevertheless included in the verifier image:
`tests/Dockerfile` uses `COPY . /tests/`. This creates a possible disclosure
risk for parties with access to the verifier image or build cache, but it does
not demonstrate access by the candidate under the configured separation.

The installed Harbor configuration and runtime did not expose a supported
verifier-only mount or secret mechanism. A proposed alternative to compute
reference outputs in the verifier at runtime was not applied: it would not
remove the ability to reconstruct answers from the reference implementation
and hidden inputs. The image/build-cache exposure remains an **unfixed,
low-severity residual risk**.

## 6. Validation results

The following are the Copilot-reported Day 5 Harbor baseline results. They
were not independently rerun during this documentation stage.

| Candidate | Overall | Build | No-Python | Behaviour | Job UUID |
|---|---:|---:|---:|---:|---|
| Oracle | 1.0 | 1.0 | 1.0 | 1.0 | `b3d68ef9-786a-4995-aee4-07a964e8d186` |
| NOP | 0.0 | 0.0 | 0.0 | 0.0 | `921529e9-3e57-4488-9545-e4456b53c7a8` |

The reported Oracle and NOP jobs each had one trial and zero exceptions. The
Oracle's behavior score of 1.0 is consistent with all 4,400 hidden cases being
matched. The NOP returned behavior 0.0; because it produced no valid Go
program, it did not provide 4,400 output lines for positional comparison.

## 7. Stage D — Attack evaluation

The historical attacks and rewards are listed in Section 2. They describe
pre-hardening results and must not be interpreted as current measurements.

Current attack measurements were not obtained. Inspection of the installed
Harbor CLI and agent implementation found no documented runner for selecting
`cheat/solve.sh` as a candidate solution. Harbor's Oracle agent selects the
task's `solution/` script; the generic custom-agent option requires an
importable agent and is not a runner for a shell solution script.

No attack job was launched. No current attack score, job UUID, or attack job
folder is available, and no attack is claimed to have been defeated.

## 8. Remaining limitations and lessons

- The expected-answer fixtures remain in the verifier image. The candidate
  separation boundary was preserved, but image/build-cache access remains a
  residual risk.
- Historical attack scores are report-derived, not independently reproduced.
  The available attack scripts do not provide a documented Harbor execution
  path, so current attack effectiveness remains unmeasured.
- Reward should depend on correct behavior rather than independent build or
  policy checks; those checks are still useful as separate reports.
- A larger, deterministic examination gives reproducible evidence across
  diverse rule interactions, while exact positional comparison prevents
  reordered or missing outputs from receiving full credit.
- A security change should use a documented Harbor mechanism and preserve the
  validated Oracle/NOP boundary. An unsupported change was not substituted for
  a measured fix.
