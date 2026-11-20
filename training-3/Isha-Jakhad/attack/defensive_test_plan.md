# Defensive Evaluation Plan

## Scope

This plan is based on [`visible_findings.md`](visible_findings.md) only. It proposes evaluator hardening; it does not use hidden test data, modify the target task, or describe a submission implementation.

## Why a small lookup is not a general implementation

A program that memorizes a finite set of exact input/output pairs can return correct results for those keys, but it does not implement the title-casing rules for arbitrary titles. An unseen word, punctuation pattern, capitalization pattern, or whitespace variation may not match any stored key. The task requires general behavior, so matching a few known examples is not evidence of correctness.

## Defensive test coverage

Generate or select a blinded, non-public evaluation set from a pinned reference implementation and include categories such as:

- **Unseen words:** held-out vocabulary and combinations not used in examples or development inputs.
- **Punctuation:** punctuation adjacent to words, apostrophes, hyphens, and colons.
- **Capitalization:** lowercase, mixed-case, uppercase, and acronym-containing titles.
- **Whitespace:** repeated spaces, tabs, leading/trailing whitespace, blank lines, and relevant line-ending forms.
- **Multiple input lines:** varied titles in one stream, including cases with distinct expected outputs, to verify ordering and one-result-per-input behavior.

Pin the reference version and mode before generating expected outputs. Keep the held-out inputs and expected outputs inaccessible to the agent until evaluation. Do not rely only on output diversity: distinct inputs can legitimately have the same expected output.

## Detecting constant-output behavior

Use a batch containing inputs whose reference outputs are known to differ, and compare every output line with the corresponding expected line. Require the number of output lines to equal the number of input records. A program that repeats one fixed string will fail cases whose expected results differ; checking only whether output is non-empty or whether it has multiple unique values is insufficient.

## Why build and cleanup are not functional evidence

According to [`visible_findings.md`](visible_findings.md), `tests/build.py:11-18` awards its criterion based on build success, and `tests/no_python.py:17-24` checks `.py` removal plus build success. Neither evaluates title-casing behavior. These checks can measure buildability and cleanup, but should not be treated as proof that the program produces correct results.

## Behaviour-evaluator improvements

The current behavior check in [`target/tests/behaviour.py`](target/tests/behaviour.py), lines 36–44, scores matching pairs using `zip` and divides by the expected-line count. Harden it by:

1. Checking input and output record counts explicitly; fail functional evaluation on missing or extra output lines.
2. Comparing the complete output sequence with the expected sequence, rather than silently ignoring unpaired trailing actual lines.
3. Keeping functional correctness as the decisive criterion. Build and cleanup checks may remain separate diagnostics, but should not substitute for correct behavior.
4. Using a larger, blinded set with diverse word, punctuation, capitalization, whitespace, and multi-line cases.
5. Pinning the reference implementation and its mode so expected outputs are reproducible.

## Recommended defensive changes

- **Exact output length and comparison:** Update [`target/tests/behaviour.py`](target/tests/behaviour.py), lines 36–44, to reject a line-count mismatch and require exact sequence equality.
- **Avoid standalone functional credit for build/cleanup:** Review [`target/tests/build.py`](target/tests/build.py), lines 11–18, and [`target/tests/no_python.py`](target/tests/no_python.py), lines 17–24, so their results cannot be mistaken for behavior correctness or replace the behavior criterion.
- **Align Python policy and environment:** Review [`target/tests/no_python.py`](target/tests/no_python.py), lines 9–13, together with [`target/environment/Dockerfile`](target/environment/Dockerfile), lines 3–5. The check scans repository `.py` files while the image installs Python; make the intended policy and enforcement consistent.
- **Specify reference semantics:** Clarify the reference mode and input/output edge cases in [`target/instruction.md`](target/instruction.md), lines 4, 7, and 17.
- **Restrict unnecessary network access:** Reconsider the public network settings in [`target/task.toml`](target/task.toml), lines 13–16 and 24–25, if the task does not require network access. The configuration alone does not establish that any particular data can be downloaded.

## Runtime-access caveat

The findings establish visible checker behavior and configuration only. They do not establish which test files an agent can access while working, whether a particular runtime path is available, or whether public networking enables a specific download.
