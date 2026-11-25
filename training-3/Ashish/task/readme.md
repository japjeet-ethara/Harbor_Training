# titlecase-go

A Harbor task: port `titlecase()` from python-titlecase 2.4.1 to Go, using only
the Go standard library, and reproduce its output byte for byte.

The agent gets a pristine copy of the original Python source in
`/workspace/repo` and writes a Go module there. The program reads one title per
line on standard input and writes one titlecased line to standard output.

## Which original

`titlecase()` behaves differently depending on whether the optional `regex`
package is installed. **The answers for this task come from titlecase WITHOUT
the `regex` package** (`import re as regex`, `REGEX_AVAILABLE` is `False`), the
same statement as `instruction.md`. On the graded inputs the two modes disagree
on 6,583 of 100,000 lines, so the mode is not a detail.

## How the score works

Grading runs in a separate container that the agent never sees. Two gates and
one scored check, the same as `instruction.md` states:

- a `.py` file left under `/workspace/repo` scores 0
- a failing `go build ./...` scores 0
- otherwise the score comes only from output correctness on 100,000 hidden
  titles; passing the two gates is worth nothing on its own
- partial credit exists only near the top: below a 90% line match rate the
  score is 0, and 1.0 requires byte-exact output on the whole stream

## Layout

```
instruction.md          what the agent is asked to do, including the mode
task.toml               schema, timeouts, separate verifier, no network
environment/Dockerfile  golang:1.23 with every interpreter removed
environment/python-titlecase/   the vendored pristine 2.4.1 snapshot (MIT)
solution/solve.sh       the oracle: the real Go port
tests/test.sh           grading entry point
tests/checks/           no_python.sh, build.sh, behaviour.sh
tests/data/             inputs.txt and answers.txt, 100,000 lines each
```

## Hardening

This task was attacked on Day 4 and hardened on Day 5. What the attacks were,
how each one was closed, the before-and-after exam numbers and the bugs the new
exam found in my own port are all in [../HARDEN.md](../HARDEN.md).
