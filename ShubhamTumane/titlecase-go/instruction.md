# Port python-titlecase to Go

## Background
The repository in `/workspace/repo` contains `python-titlecase`, a Python library that applies capitalization rules to convert English text into title case following common style conventions (handling stop words, boundary words, acronyms, colons/punctuation, hyphens, and apostrophes/contractions).

## Task
You must create a standalone Go implementation in `/workspace/repo` that performs the exact same title-casing transformation as the original Python library.

The Go application must be a command-line tool that:
- Reads input titles from standard input (`stdin`), one title per line.
- Writes the converted titlecased result to standard output (`stdout`), one title per line.

## Hard Rules
1. **Go Standard Library Only**: You may only use the Go standard library. External third-party Go packages or modules are strictly forbidden.
2. **Remove All Python Files**: No `.py` files may remain anywhere in `/workspace/repo`. Every Python source file, test file, and configuration script must be deleted before completion.
3. **Compilation**: The command `go build ./...` must succeed without errors inside `/workspace/repo`.
4. **Exact Behavior**: The converted output must match the original Python `titlecase()` output byte for byte across all test titles.

## Evaluation
Your solution will be evaluated automatically by running hidden test inputs against your compiled Go program and checking compilation, repository cleanup, and exact line-by-line output matching.