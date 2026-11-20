# Day 4 Experiment Plan

**Target:** `ShubhamTumane/titlecase-go/`  
**Scope:** Proposed robustness checks only. No tests, hidden data, reference answers, or solution files were accessed, and Harbor was not run.

The task requires a Go command-line program to read one title per stdin line and write the corresponding title-cased result per stdout line, matching the original Python `titlecase()` behavior byte for byte. The visible behavior criterion is described in [`tests/behaviour.py`](../../ShubhamTumane/titlecase-go/tests/behaviour.py); the task contract is in [`instruction.md`](../../ShubhamTumane/titlecase-go/instruction.md).

## 1. Line and stream handling

- **Objective:** Check that the CLI consistently maps input lines to output lines.
- **Input categories:** Empty input; one ordinary title; multiple titles; blank lines between titles; input with and without a final newline; LF and CRLF line endings.
- **Expected behaviour:** Transform each title according to the original Python reference behavior, preserve input order, and emit one result line for each input title. Exact title-casing is subject to the selected reference mode.
- **Visible criterion:** Behavior matching in `tests/behaviour.py`.
- **Evidence to record:** Input category, number and order of input lines, number and order of output lines, and a mismatch summary against the selected reference behavior.
- **Possible limitations:** The task specifies one title per line but may not fully define treatment of blank lines or platform-specific line endings. A small corpus cannot establish correctness for all inputs.

## 2. Reference-mode consistency

- **Objective:** Check whether the expected behavior is reproducible when the optional `regex` dependency changes the Python reference implementation's behavior.
- **Input categories:** A small, non-hidden sample of ordinary titles and titles with punctuation or word boundaries relevant to the library's rules.
- **Expected behaviour:** Results should match the original Python implementation in the mode selected for grading. If the two dependency modes produce different results, the task needs to identify which mode is authoritative; the task instruction currently requires matching the original but does not state a mode.
- **Visible criterion:** Behavior matching in `tests/behaviour.py`.
- **Evidence to record:** Reference implementation version, dependency mode, whether repeated runs are stable, and a count of differences between modes. Do not use or record hidden test data or hidden expected outputs.
- **Possible limitations:** This check can identify mode ambiguity but cannot establish which mode the grader uses without an explicit task or grader declaration.

## 3. Character-boundary coverage

- **Objective:** Check that capitalization behavior holds across character and punctuation boundaries.
- **Input categories:** Non-ASCII letters; punctuation adjacent to words; apostrophes and contractions; hyphenated words; acronyms; stop words and boundary words in varied positions.
- **Expected behaviour:** For the selected reference mode, output should match the original Python implementation byte for byte. Do not assume a generic title-casing convention where the reference behavior is authoritative.
- **Visible criterion:** Behavior matching in `tests/behaviour.py`.
- **Evidence to record:** Categories exercised, reference mode, mismatch count, and a concise summary of any mismatches using only the non-hidden sample.
- **Possible limitations:** A limited set of examples cannot cover all Unicode, locale, or punctuation interactions. The task instruction does not enumerate every rule or character class.

## Execution status

These are proposals, not executed tests. No Harbor run was performed, no files in the target task were changed, and no solution scripts were created.
