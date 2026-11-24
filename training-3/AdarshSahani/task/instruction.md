# Repository description

## Frozen oracle mode and dataset provenance

The frozen expected-answer files correspond to the original Python
implementation with the optional third-party `regex` package unavailable
(`REGEX_AVAILABLE = False`, so the implementation uses Python's built-in
`re` fallback). This mode was confirmed by two fresh runs of `tests/gen.py`:
both regenerated all four checked-in files byte-for-byte after normalizing
their CRLF line endings. The current generator is fixed at 2,000 visible and
2,000 hidden records; it does not produce the Day 5 requirement of 100,000
input/answer records. See `measure/generation-verification.json` and
`HARDEN.md` for hashes and limitations.

The original python-titlecase project is the Python implementation of a title-casing function based on John Gruber's Perl implementation. It is version 2.4.1 from https://github.com/ppannuto/python-titlecase, licensed under the MIT License and copyrighted by Patrick William Pannuto.

# What to build

Implement a Go program in /workspace/repo that reads one title per line from stdin and prints the title-cased result, one per line.

# Hard rules

- Use the Go standard library only.
- No Python files may remain anywhere in /workspace/repo.
- go build ./... must pass.

# Behaviour

The Go implementation must match the original Python titlecase() output byte for byte for every input.

# Not checked

- Speed.
- Memory usage.
- Error message wording.

# Grading

Build success and removal of Python files are required conditions, not independent reward components. The reward is behavioral accuracy above the identity-output baseline, normalized to 0–1: a perfect implementation scores 1, and a program that only echoes input scores 0. Partial credit remains available for improvements over echo.
