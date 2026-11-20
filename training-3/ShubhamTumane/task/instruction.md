# Port python-titlecase to Go

## Background
The repository in `/workspace/repo` contains `python-titlecase`, a Python library that applies capitalization rules to convert English text into title case following common style conventions (handling stop words, boundary words, acronyms, colons/punctuation, hyphens, and apostrophes/contractions).

## Task
You must create a standalone Go implementation in `/workspace/repo` that performs the exact same title-casing transformation as the original Python library (`titlecase.__init__.titlecase` running in standard-library `re` mode, i.e., `REGEX_AVAILABLE = False` without the optional third-party `regex` package).

The Go application must be a command-line tool that:
- Reads input titles from standard input (`stdin`), one title per line.
- Writes the converted titlecased result to standard output (`stdout`), one title per line (exact same line count as input; no extra lines).

## Hard Rules
1. **Go Standard Library Only**: You may only use the Go standard library. External third-party Go packages or modules are strictly forbidden.
2. **Remove All Python Files & No Python Runtime Calls**: No `.py` files may remain anywhere in `/workspace/repo`, and the Go program must not invoke Python or external interpreters at runtime.
3. **Compilation**: The command `go build ./...` must succeed without errors inside `/workspace/repo`.
4. **Exact Behavior**: The converted output must match the original Python `titlecase()` output (`re` stdlib mode) byte for byte across all test titles.

## Evaluation
Your solution will be evaluated automatically against a hidden 100,000-title test suite checking compilation, repository cleanup, and exact line-by-line output matching on non-trivial transformations.