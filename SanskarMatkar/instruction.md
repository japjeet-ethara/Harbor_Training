# Port python-titlecase to Go

## 1. The repository

`/workspace/repo` contains **python-titlecase 2.4.1**, a small MIT-licensed Python library (a port of John Gruber's `titlecase.pl`). Its function `titlecase(text)` in `titlecase/__init__.py` turns a phrase into a headline: it lower-cases small words such as *a*, *of* and *the* (but capitalises them at the start and end of the title and after `:`-style sub-phrase punctuation), keeps words like `iPhone`, `example.com` and `U.S.` as they are, handles `O'Neil`/`d'Artagnan`, `McDonald`, `Mr`/`Dr`, slashes and hyphens, guesses all-consonant acronyms like `CNN`, and preserves the original whitespace exactly.

## 2. What to build

Replace the Python library with a **Go program** in `/workspace/repo`:

- `/workspace/repo` must be a Go module (a `go.mod` at its root) whose **root package is `package main`**, so that `cd /workspace/repo && go build -o titlecase .` produces the program.
- The program reads **standard input** as UTF-8 text, **one title per line** (lines end with `\n`).
- For every input line it writes the titlecased result followed by `\n` to **standard output**, in the same order — exactly one output line per input line, including for empty or whitespace-only lines. Nothing else is written to standard output.

## 3. Hard rules

- **Go standard library only.** No third-party modules. The grader builds with the Go 1.23 toolchain that is already installed, with no network access (`GOTOOLCHAIN=local`, `GOPROXY=off`), so the `go` directive in `go.mod` must not be newer than `1.23`.
- **No `.py` files may be left anywhere under `/workspace/repo`** (including in subdirectories) when you finish. The Python implementation is replaced, not kept alongside.
- `cd /workspace/repo && go build ./...` must succeed.

## 4. Behaviour

For every input line, the output must be **byte-for-byte identical** to what the original Python function returns for that line, called as `titlecase(line)` with all default arguments (no callback / wordlist, `small_first_last=True`), using the code exactly as it is in this repository **with only the Python standard library installed** — i.e. the optional `regex` package is *not* available, so the module's `re` fallback patterns apply.

Inputs are valid UTF-8 and contain no `\r` or `\n` inside a line. Besides ASCII (letters, digits, punctuation, spaces and tabs) they may contain accented Latin letters (e.g. `é`, `Ñ`), typographic quotes and dashes (`‘ ’ “ ” – — …`), and non-ASCII spaces such as the no-break space (U+00A0) and the thin space (U+2009). Python 3 string semantics apply: `\w`, `\s`, `\b`, `upper()`, `lower()` and `capitalize()` are Unicode-aware.

Note that Go's `regexp` package does not support look-ahead, look-behind or back-references, and its `\w`, `\s` and `\b` are ASCII-only, so the Python patterns cannot simply be copied.

## 5. Not checked

Speed (within a generous time limit), memory use, code style, the wording of any error messages, and anything written to standard error.

## 6. How it is graded

Hidden automatic tests run after you finish, in a separate container. They give a **partial score** made of three weighted parts: the module builds, no `.py` files remain (only counted if the build passes), and the share of a hidden set of titles for which your program's output line exactly matches the original Python output (the largest part).
