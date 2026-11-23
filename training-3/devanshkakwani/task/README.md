# Titlecase in Go

This Harbor task ports the rule-based Python `titlecase()` behavior to a
Go command-line program. The program reads UTF-8 text from standard input,
title-cases each line, and writes the result to standard output. It uses only
the Go standard library.

## Requirements

- Go 1.23 or later
- Harbor, if you want to run the task through the benchmark harness

## Build and run

From this directory:

```sh
go build ./...
go run . <<'EOF'
the quick brown fox
war and peace
EOF
```

Expected output:

```text
The Quick Brown Fox
War and Peace
```

The task specification and behavioral requirements are in
[`instruction.md`](instruction.md). The reference task environment, solution,
cheat example, backup, verifier, and fixtures are retained in their respective
directories. The four verifier data files are under `tests/data/`.

## Implementation notes

`main.go` reads standard input, splits it into lines, preserves whitespace,
and applies the title-casing rules in order. The rules cover small words,
initials, apostrophe forms, `Mc` prefixes, honorifics, existing capitals,
compounds, acronyms, punctuation, and sub-phrases. Unicode letter and case
handling uses the standard `unicode` package.

The canonical real solution is `solution/solve.sh`. The separate
`cheat/solve.sh` is retained as a negative example; it is not the task solution.

## Verifier and scoring

The verifier defines three criteria in `tests/`:

| Criterion | Weight | Check |
| --- | ---: | --- |
| `build` | 1 | `go build ./...` succeeds. |
| `no_python` | 1 | No Python source is present in the submitted workspace, the Go build succeeds, and the executable returns exact expected output for two stdin cases. |
| `behaviour` | 4 | Fraction of output lines matching the hidden expected output. |

The overall reward is the weighted mean:

```text
(build * 1 + no_python * 1 + behaviour * 4) / 6
```

For detailed verifier behavior and recorded run results, see
[`CONTEXT.md`](CONTEXT.md). The grader's hidden fixtures are used by the
behavior criterion; do not use visible expected output as a substitute for
processing input.

## Run with Harbor

From the task directory, the recorded benchmark commands are:

```sh
harbor run -p . -a oracle
harbor run -p . -a nop
```

`tests/test.sh` is the verifier entry point inside its configured test
container; it invokes Reward Kit against `/workspace/repo`.
