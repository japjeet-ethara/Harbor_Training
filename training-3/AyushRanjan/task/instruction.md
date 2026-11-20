# Titlecase in Go

## Repository

This repository is a Python titlecase library. Its `titlecase` function converts a line of text to title case, applying the library's rules for small words, abbreviations, punctuation, and related cases. Those rules are defined by the Python implementation in this repository.

## What to build

Implement an equivalent titlecase program in Go in `/workspace/repo`. The program must read one title per line from standard input and write the corresponding titlecased result to standard output, one result per line.

## Requirements

- Use only the Go standard library.
- The solution must not contain or use any `.py` files.
- `go build ./...` must pass.
- For the provided inputs, the Go output must match the original Python library's `titlecase` behavior byte for byte.

## Reference behavior and evaluation data

- Reference mode: the bundled Python `titlecase` implementation **without the optional `regex` module** (`REGEX_AVAILABLE=False`). The titlecase source falls back to Python's standard `re` module in this mode.
- The verifier evaluates 100,000 deterministic, unique input lines from `tests/data/inputs.txt`, generated with seed 1. `tests/data/answers.txt` contains the corresponding frozen reference output.
- The original 2,000 hidden regression cases are also retained under `tests/data/legacy-2k/` and checked after the 100K exam.
- The verifier gives behavior credit only when the complete output has the same number of lines and every output line matches its reference answer exactly.
- The expected-answer file is verifier-only. The candidate receives inputs through standard input and must write results to standard output.

## Not graded

Execution speed, memory usage, and exact error messages are not required to match.

## Grading

The task is evaluated with hidden automatic tests. Partial credit is possible.
