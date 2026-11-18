# Repository description

The original `python-titlecase` project is the Python implementation of a title-casing function based on John Gruber's Perl implementation. It is version 2.4.1 from `https://github.com/ppannuto/python-titlecase`, licensed under the MIT License and copyrighted by Patrick William Pannuto.

# What to build

Implement a Go program in `/workspace/repo` that reads one title per line from stdin and prints the title-cased result, one per line.

# Hard rules

- Use the Go standard library only.
- No Python files may remain anywhere in `/workspace/repo`.
- `go build ./...` must pass.

# Behaviour

The Go implementation must match the original Python `titlecase()` output byte for byte for every input.

# Not checked

- Speed.
- Memory usage.
- Error message wording.

# Grading

Hidden automatic tests provide partial credit according to behavioural accuracy.
