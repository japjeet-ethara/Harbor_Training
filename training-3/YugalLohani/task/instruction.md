# Port python-titlecase to Go

## 1. The repository

`/workspace/repo` contains python-titlecase 2.4.1 (MIT licence, commit
`42f43e2de55bf003b286c6f8e8d8b2d26676a167`), a Python port of John Gruber's
`titlecase.pl`. Its function `titlecase(text)` converts text to title case: small words
such as "of" and "the" stay lower case except at the start and end of a line, words with
inner capitals or inline periods are kept as they are, all-consonant words become
acronyms, and there are special rules for "Mc", "O'Neil", hyphens and slashes. All of the
logic is in `titlecase/__init__.py`.

## 2. What to build

Replace the Python code with a Go program in `/workspace/repo`. Running

```
cd /workspace/repo && go build -o /tmp/titlecase .
```

must produce a program that reads text from standard input, one title per line, and for
each input line writes the title-cased line followed by `\n` to standard output, in the
same order. It must work when started from any working directory.

Every input line ends with `\n`, is valid UTF-8, and contains no `\r`. A line may be empty
and may contain any other Unicode characters, including Unicode spaces and tabs.

## 3. Required behaviour

For every input line, the output line must be identical, byte for byte, to what the
original returns for that line:

```python
from titlecase import titlecase
titlecase(line)          # default arguments: no callback, no word list
```

The reference is the code at the commit above, run on CPython 3.12 (Unicode 15.0) with
the `regex` package version 2024.11.6 installed, so the module uses its `regex` patterns
(`REGEX_AVAILABLE` is `True`). Note that the `python3` in this environment is version 3.11
without `regex`, so running the original here takes the other code path and gives
different answers for some lines.

## 4. Hard rules

- Go standard library only: `go.mod` has no `require` lines and there is no `vendor/`
  folder.
- Use the Go 1.23 toolchain installed here (`GOTOOLCHAIN=local`); `go.mod` must not ask
  for a newer Go version.
- When you finish, there must be no `.py` file anywhere under `/workspace/repo`.
- `go build ./...` in `/workspace/repo` must succeed.
- Only `/workspace/repo` is kept for grading. Files elsewhere (`/tmp`, your home folder,
  settings made with `go env -w`) are not. The program must not need the network.

## 5. Not checked

Speed and memory (beyond a limit of 60 seconds for a few thousand lines), standard
error, exit codes, error messages, input that does not end with `\n`, and invalid UTF-8.

## 6. Grading

Grading is automatic and gives partial credit. It checks that the module builds with the
standard library only, that no `.py` file remains, and compares your program's output,
line by line, with the original's on a large set of inputs that you do not see.
