# Port pyfiglet to Go

## The repository

`/workspace/repo` is a checkout of pyfiglet at commit `255827efbc09d662875dad50fa0edc1e1263bf45`, a pure-Python FIGlet implementation released under the MIT licence. It parses `.flf`/`.tlf` font files, renders each input character as a block of ASCII art, and joins the blocks with kerning or smushing. It also wraps text, justifies it, mirrors it, flips it, and can print right-to-left. The Python source is the specification for this task.

## What to build

Build a Go command-line program in `/workspace/repo`. From `/workspace/repo`, `go build -o /tmp/figlet .` must produce the executable `/tmp/figlet`.

The program accepts options followed by text:

```
/tmp/figlet [options] TEXT...
```

These options must work:

- `-f FONT` (default `standard`): select the font named `FONT` from the font files in the repository.
- `-w COLS` (default `80`): width used for wrapping and for justification.
- `-j auto|left|center|right` (default `auto`): justification. `auto` means `left` for left-to-right and `right` for right-to-left. `center` prepends `int((COLS - len(row)) / 2)` spaces to each rendered row; `right` prepends `COLS - len(row) - 1` spaces. These use the current `-w COLS`, not a fixed 80.
- `-D auto|left-to-right|right-to-left` (default `auto`): print direction. `auto` uses the font file's default direction.
- `-r`: mirror the finished output horizontally.
- `-F`: flip the finished output vertically. If both `-r` and `-F` are given, apply `-r` first, then `-F`.
- `-s`: strip empty lines before and after the rendered block.
- `-n`: put exactly one empty line before and one after the rendered block. If both `-s` and `-n` are given, `-s` takes precedence.
- All remaining arguments are the text and are joined with one ASCII space, as pyfiglet does.

The output must match the original Python pyfiglet byte for byte for every checked input, including wrapping, kerning, smushing, the font header's hardblank character, and the exact spacing produced by `-j` and `-w`.

## Fonts

The `.flf` files may be moved inside the repository, but they must remain in the repository. `/tmp/figlet` must work from any current working directory; it must not depend on being run from `/workspace/repo`.

## Hard rules

- Use only the Go standard library.
- When you are done, no `.py` file may exist anywhere under `/workspace/repo`.
- `go build ./...` must pass in `/workspace/repo`.

## Not checked

- Speed and memory use.
- The wording of error messages.
- The options `-c`, `-L`, `-l`, and `-i`; you do not need to implement them.
- Behaviour when no text argument is supplied.

## Grading

Grading runs hidden automatic cases and awards partial credit for each case whose output matches exactly. A solution that builds but renders incorrectly receives partial credit; a solution that does not build receives none.

## Definition of done

- `go build ./...` passes in `/workspace/repo`.
- `go build -o /tmp/figlet .` produces `/tmp/figlet`.
- `/tmp/figlet` renders the checked option combinations byte-for-byte like pyfiglet.
- `/tmp/figlet` works from a different working directory.
- No `.py` file remains under `/workspace/repo`.
