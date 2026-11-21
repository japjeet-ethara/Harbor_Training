# Port python-titlecase to Go

## 1. Repository

The original project is python-titlecase
(https://github.com/ppannuto/python-titlecase), released under the MIT License
at commit 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (2024-04-05). A copy of it,
without its `.git` folder, is in `/workspace/repo`. Its `titlecase` function
(in `titlecase/__init__.py`) turns text into title case. Small words come from
the New York Times Manual of Style, plus vs and v: a, an, and, as, at, but, by,
en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. It also keeps
uppercase initials on an all-caps line, recases apostrophe words that start
with d, o, or l, capitalizes Mc names, capitalizes only the first letter of Mr,
Mrs, Ms, and Dr, leaves inline periods and existing internal capitals
unchanged, lowercases small words, title-cases the parts of a single slash or a
hyphen separately, lowercases a remaining word on an all-caps line before
capitalizing it, uppercases a consonant-only acronym longer than two letters,
capitalizes any other word, capitalizes a small word at the start or end of a
line and after a subphrase break, and keeps the original space characters.

## 2. What to build

Replace the Python library with a **Go program** in `/workspace/repo`.

- `/workspace/repo` must be a Go module (it must contain `go.mod`).
- The module root must be a `main` package, so that `go build -o <binary> .`
  run in `/workspace/repo` produces the program.
- The program reads **standard input**, one title per line, and writes the
  titlecased result to **standard output**, one line per input line, in the same
  order. Each output line ends with `\n`. Input lines end with `\n`.

## 3. Hard rules

- Use the **Go standard library only** (no third-party modules).
- `/workspace/repo` must be a **single Go module**: exactly one `go.mod`, at the root.
- The program must **not start another process and must not step outside the Go
  memory model**. Do not import `os/exec`, `syscall`, `unsafe`, `plugin` or
  `runtime/cgo`, do not call `os.StartProcess`, and do not use `go:linkname`.
  (cgo is off.) In particular you may not shell out to Python or any other tool.
- When you are finished, **no `.py` files may be left anywhere** under
  `/workspace/repo`.
- `go build ./...` run in `/workspace/repo` must succeed.

## 4. Required behaviour

For every input line, the output line must be **byte for byte identical** to
what the original Python function returns for that line when called with
default arguments, `titlecase(line)`: no callback, `small_first_last=True`,
`preserve_blank_lines=False`, `normalise_space_characters=False`.

**Mode (which original).** The reference answers come from titlecase run
**WITHOUT the optional `regex` package** — plain Python `re`, with
`REGEX_AVAILABLE = False` — and no wordlist file. This is how the library behaves
on a plain `pip install titlecase`. On a handful of inputs the two modes disagree;
only the plain-`re` answer is accepted here.

This must hold for every input, including Unicode text, punctuation, all-caps
lines and unusual whitespace inside a line.

## 5. Not checked

Speed, memory use, code style, and the wording of any error messages are not
checked.

## 6. How it is graded

Your work is graded by hidden automatic tests after you finish. The score is the
**share of hidden input lines whose output matches the original exactly**. The
hard rules in section 3 are gates: if the build fails, any `.py` file remains, or
the program uses a forbidden package / starts a process, the score is **0**.
There is no partial credit just for building or for deleting the Python.
