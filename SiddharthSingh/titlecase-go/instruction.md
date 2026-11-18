# Titlecase Go Port

## 1. Background
The repository currently contains `python-titlecase`, a Python implementation of John Gruber's titlecasing algorithm originally written in Perl and maintained for Python by Stuart Colville and Patrick William Pannuto. It applies capitalization rules for English titles, intelligently preserving small words (such as articles, short prepositions, and conjunctions), honorifics, acronyms, and technical compounds like URLs and file extensions.

## 2. Objective
Build a command-line Go application in `/workspace/repo` that reads titles line-by-line from standard input (`stdin`) and prints the titlecased result to standard output (`stdout`), one title per line.

## 3. Hard Rules
- **Go Standard Library Only**: You may only use the Go standard library. Third-party packages or external modules are forbidden.
- **`go build ./...` must succeed**: The Go module and program must build cleanly without warnings or errors.
- **No Python Files**: All `.py` files must be completely removed from `/workspace/repo` before completion. No `.py` files may remain anywhere in the repository.

## 4. Expected Behavior
- The output of the Go program must match the output of the original Python `titlecase()` function byte-for-byte for every input line.
- Each line read from `stdin` should be processed and printed to `stdout` followed by a newline.

## 5. Exclusions
- Execution speed, memory usage, and error message wording are not evaluated.

## 6. Evaluation
Your solution will be evaluated by hidden automated tests that check build success, verify the absence of Python files, and compare output line-by-line against reference outputs. Partial credit is awarded based on test criteria.

