# Port python-titlecase to Go

## Context
`python-titlecase` is a Python port of John Gruber's titlecasing algorithm that capitalizes English text according to style guide conventions (such as the New York Times Manual of Style). It intelligently capitalizes titles while keeping small words (such as articles, short conjunctions, and prepositions) in lowercase unless they appear as the first or last word of a phrase, handles acronyms and mixed-case terms, supports hyphens and slashes, and correctly formats title abbreviations and name prefixes (such as Mc, Mac, and apostrophe prefixes).

## Deliverable
Implement a Go command-line tool directly within `/workspace/repo`. The tool must read text lines from standard input (`stdin`) and write the titlecased version of each line to standard output (`stdout`), processing input line-by-line (one line of output per input line).

## Hard Constraints
- **Standard Library Only**: Use only the Go standard library (`go` standard packages). External Go dependencies, third-party libraries, or external modules are strictly prohibited.
- **Clean Compilation**: Running `go build ./...` inside `/workspace/repo` must succeed without any warnings or errors and produce a valid executable.
- **Remove Python Files**: All Python source and configuration files (any file ending in `.py`) must be completely removed from `/workspace/repo`.

## Behavioral Parity
The output of your Go command-line tool must match Python `titlecase.titlecase()` byte-for-byte on every input line. Your implementation must reproduce all standard titlecasing rules and edge cases, including:
- Keeping small words lowercase in internal positions.
- Always capitalizing the first and last words of a title/phrase.
- Capitalizing words immediately following sub-phrase punctuation (such as colons, semicolons, em-dashes, en-dashes, and hyphens).
- Lowercasing lines that are written entirely in all-caps before applying titlecase rules.
- Capitalizing consonant-only acronyms (greater than 2 characters).
- Preserving terms with inline periods (e.g., domain names, URLs, filenames).
- Preserving mixed-case, CamelCase, and words with uppercase letters elsewhere.
- Recursively titlecasing hyphen- and slash-separated compounds.
- Correctly formatting `Mc` and `Mac` name prefixes.
- Correctly formatting surnames with apostrophe prefixes (e.g., `O'`, `d'`, `l'`).
- Capitalizing common title and honorific abbreviations (`Mr`, `Mrs`, `Ms`, `Dr`).
- Preserving dotted uppercase initials in all-caps lines.

## Non-Requirements
Execution latency, internal memory usage, and debugging log messages written to `stderr` are not evaluated.

## Grading Summary
Your solution will be graded automatically against a hidden test suite with partial scoring:
- Clean build of the Go codebase via `go build ./...`.
- Verification that all `.py` files have been removed from `/workspace/repo`.
- Exact behavioral parity across diverse inputs against the reference implementation.
