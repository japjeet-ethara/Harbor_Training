# Task context and validation

## What the task does

The task asks for a Go implementation of the Python `titlecase()` behavior.
It reads UTF-8 text from standard input, processes one title per line, and
writes the title-cased lines to standard output. It is intended to reproduce
the reference rules for whitespace, small words, initials, apostrophes,
prefixes, honorifics, compounds, acronyms, punctuation, and sub-phrases.

## How the Go implementation works

`main.go` reads all standard input, rejects invalid UTF-8, splits the input
into lines, and processes each line independently. It preserves whitespace
between words and applies ordered helpers for the title-casing rules. Unicode
letter checks and simple case mappings use Go's standard library. The module
has no third-party Go dependencies.

`solution/solve.sh` is the canonical real solution. `cheat/solve.sh` is kept
separately as a negative example and is not the submitted solution. The
`backup/` copy is retained as requested.

## How Reward Kit scores the task

`tests/reward.toml` configures a weighted mean with these criteria:

| Criterion | Weight | Scoring behavior |
| --- | ---: | --- |
| `build` | 1 | Passes if `go build ./...` succeeds. |
| `no_python` | 1 | Passes only if the submitted workspace has no `*.py` files, the Go package builds, and the compiled executable exits successfully with exact output for both stdin samples. |
| `behaviour` | 4 | Returns the fraction of output lines equal to the hidden expected lines; build or execution failure scores zero. |

The aggregate reward is `(build + no_python + 4 * behaviour) / 6`. The
behavior criterion compares line counts as well as line contents, using the
larger of the expected and actual output counts as its denominator.

## Why `no_python` checks real stdin behavior

A file-extension scan and a successful Go build do not prove that the
executable implements the task. A program could build while ignoring stdin
and printing a known, visible expected-output file. The `no_python` criterion
therefore also runs the compiled executable on two specific stdin inputs and
compares its exit status and complete stdout byte-for-byte with the expected
responses. This rejects a visible-answer dumper that does not actually
process input.

## Recorded validation results

These are the available Harbor run results recorded with the local project:

| Run | Trials | Exceptions | Mean reward |
| --- | ---: | ---: | ---: |
| Oracle (perfect run) | 1 | 0 | 1.000 |
| Nop | 1 | 0 | 0.000 |
| Oracle (additional recorded run) | 1 | 0 | 0.167 |

The additional Oracle-labeled run is reported separately rather than
discarded; its reason for differing from the perfect run is not recorded.

No Harbor run result for the cheat agent is available in the local project,
so no numeric cheat reward is claimed. By inspection, `cheat/solve.sh`
generates a program that prints the visible expected-output file instead of
processing stdin. That strategy fails the two exact stdin checks in
`no_python`; its overall Harbor score was not measured here.

The four test data files are retained unchanged in `tests/data/`:
`inputs.txt`, `expected.txt`, `hidden_inputs.txt`, and `hidden_expected.txt`.
