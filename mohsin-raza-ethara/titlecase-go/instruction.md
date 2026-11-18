# Reimplement python-titlecase in Go

## 1. The repository

`/workspace/repo` is a checkout of **python-titlecase**, the Python library by
Patrick Pannuto that implements John Gruber's title-casing algorithm (MIT
licensed, version 2.4.1). Its core is `titlecase/__init__.py`, whose
`titlecase()` function capitalises words while keeping small words (`a`, `an`,
`and`, `the`, `of`, `in`, …) lower-case except at the start or end of a line and
after sub-phrase punctuation; it preserves words containing inline periods or
internal capitals, special-cases `Mc`/`Mac` prefixes and titles such as Dr, Mr,
Mrs, Ms, apostrophe-second words, all-caps lines and initials, and
consonant-only acronyms, and it recursively handles slash- and hyphen-separated
compounds. The exact reference behaviour is defined solely by that function with
its default arguments: `callback=None`, `small_first_last=True`,
`preserve_blank_lines=False`, `normalise_space_characters=False`.

## 2. What to build

Replace the Python implementation with a **Go program** in `/workspace/repo`.
The program reads titles from standard input (one title per line) and writes the
titlecased result to standard output (one result per line). Only the transformed
text goes to stdout; diagnostics, if any, belong on stderr. The program must be
buildable and runnable as a normal Go command in that directory.

## 3. Hard rules

- **Go standard library only.** Do not add third-party dependencies, do not
  fetch modules, and do not vendor external code.
- **No `.py` files may be left anywhere in the repository.** You may read the
  Python source to learn the behaviour, but every Python file (including caches
  and nested directories) must be gone when you are done.
- **`go build ./...` must pass** when run from `/workspace/repo`.

## 4. Behaviour

The output must match the original Python `titlecase()` **byte for byte, for
every input** — not just visually similar. Treat the whole of stdin as the
input to `titlecase()` and the whole of stdout as its return value; differences
in letters, punctuation, whitespace (including runs of spaces and tabs), line
endings, blank-line handling, and whether the output ends with a newline all
count as failures. Note that the default behaviour drops blank lines, joins
lines with `\n`, and leaves the case of some tokens untouched; reproduce that
faithfully rather than "improving" it.

## 5. Not checked

Speed, memory usage, and the wording of error messages are not graded. Internal
structure, file layout, and naming are yours to choose.

## 6. How it is graded

Hidden automatic tests run the built program on inputs that are not shown to
you and compare stdout with the reference implementation. Grading is partial:
each case contributes independently, so implement as much of the behaviour
correctly as you can rather than optimising for a single scenario.
