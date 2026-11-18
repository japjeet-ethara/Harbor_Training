# Task: Port `titlecase` to Go

## What the repository is

`python-titlecase` (https://github.com/ppannuto/python-titlecase) is a Python library that
converts strings to title case following the rules of the New York Times Manual of Style.
It is more than a simple `str.title()` call: it keeps small words such as *a*, *an*, *and*,
*as*, *at*, *but*, *by*, *en*, *for*, *if*, *in*, *of*, *on*, *or*, *the*, *to*, *v*,
*via*, and *vs* in lowercase (unless they appear at the very start or end of a line, or
immediately after a sub-phrase delimiter such as `: ; . ? !` or an em/en dash followed by
a space). It also preserves already-mixed-case words like `iTunes` and domain names like
`example.com`, handles `Mc`/`Mac` prefixes, handles apostrophe-second words (`l'Grange`,
`O'Reilly`), treats all-consonant words longer than two characters as acronyms (e.g. `cnn`
→ `CNN`), and processes hyphenated and slash-separated phrases recursively.
The library is at `/workspace/repo` inside the container.

## What to build

Write a Go program inside `/workspace/repo` that:

1. Reads one title per line from **stdin** (UTF-8).
2. Applies title-case conversion to each line using the same rules as the Python
   `titlecase()` function (called with its default arguments).
3. Prints the converted title to **stdout**, one result per line, in the same order as the
   input.

The repository must contain a valid `go.mod` and at least one `.go` source file.
The program must be buildable with `go build ./...` using only the **Go standard library**
(no third-party modules).

## Hard rules

- **Go standard library only.** The `go.mod` file must list no external dependencies beyond
  the standard library.
- **No `.py` files anywhere under `/workspace/repo`** when the solution is complete.
  Delete every `.py` file (including `titlecase/*.py` and any test files) before finishing.
- **`go build ./...` must pass** with exit code 0 from `/workspace/repo`.

## Behaviour

The output of the Go program must match the output of the original Python `titlecase()`
function **byte for byte** for every input line. No approximation is acceptable.

## Not checked

Speed, memory usage, and the exact wording of any error messages are not evaluated.

## How it is graded

The task is graded by hidden automatic tests using weighted-mean aggregation:

- **build** (weight 1): `go build ./...` passes → full credit, otherwise zero.
- **no_python** (weight 1): `go build ./...` passes AND no `.py` files exist anywhere under
  `/workspace/repo` → full credit, otherwise zero.
- **behaviour** (weight 4): the Go program is run on a hidden set of input lines; the score
  is the fraction of output lines that exactly match the expected Python output.

Partial credit is available for the behaviour check.
