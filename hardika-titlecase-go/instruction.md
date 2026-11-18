# Port python-titlecase to Go

The repository at /workspace/repo is a pinned checkout of python-titlecase. The library applies title capitalization to Unicode text. It accounts for small words, names, initials, punctuation, compounds and the original whitespace.

Create a Go command in the repository root. Read UTF-8 titles from standard input and write their titlecased results to standard output, with a newline after each result. Handle LF and CRLF record separators, blank records and a final record without a separator. An empty stream produces no output.

Use the Go standard library. Ensure go build ./... succeeds in /workspace/repo and remove every .py file anywhere under that directory.

Match the bytes returned by the original titlecase() function with its default arguments, using CPython 3.12.14 and optional regex 2026.11.15 in VERSION0 mode. Preserve whitespace and punctuation exactly as the reference does. The environment includes that Python interpreter and regex dependency for examining the upstream behavior.

Hidden automatic checks award partial credit for a successful build, removal of Python files after a successful build, and the fraction of exact output records. Speed, memory use and error-message wording do not affect the score.
