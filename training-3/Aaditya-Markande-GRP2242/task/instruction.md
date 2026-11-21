cat > task/instruction.md <<'EOF'
# Port python-titlecase to Go

## The repository
`/workspace/repo` contains python-titlecase 2.4.1 (MIT licence). Its `titlecase()` function in
`titlecase/__init__.py` turns a title into proper title case: small words such as "of" and "the"
stay lowercase, acronyms and words like "iPhone" are kept, hyphenated and slashed words are
handled part by part, and so on. Python 3 with the `regex` module is installed, so you can run
the original, for example:

    cd /workspace/repo && python3 -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"

## What to build
A Go program whose module root is `/workspace/repo` (`go.mod` in that folder, `package main` in
the same folder). It reads standard input one title per line and writes the titlecased result to
standard output, one result per line, each ending with a newline. Input is UTF-8 text: titles can
contain Unicode letters, punctuation, tabs and other unusual spaces. The program takes no arguments.

## Mode
The expected answers come from the original `titlecase()` with its default options **WITH the
`regex` module installed** (`REGEX_AVAILABLE` is True).

## Hard rules
1. Use the Go standard library only. No third-party modules, no `vendor` folder.
2. When you finish, no file ending in `.py` may exist anywhere under `/workspace`.
3. `go build ./...` run in `/workspace/repo` must succeed.
4. The program must be self-contained. It is run alone, as an unprivileged user, in an empty
   folder: no Python, no other files, no network. The packages `os/exec`, `syscall`, `plugin`
   and `unsafe`, `import "C"`, `//go:embed` and `//go:linkname` are not allowed. All files in
   `/workspace/repo` together must stay under 400 KB.

## Behaviour
For every input line, your output must be identical, byte for byte, to what the original
`titlecase(line)` returns with its default options and the `regex` module installed.

## Not checked
Speed, memory use, error message wording, tests, documentation and code style.

## How it is graded
The score is the share of 100,000 hidden input lines whose output matches exactly, from 0 to 1.
It counts only if the build passes and the rules in "Hard rules" are met; otherwise the score is 0.
EOF