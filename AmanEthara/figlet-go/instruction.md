
# Task: The Machine That Shouts in Giant Letters

Implement a Go command-line program that reproduces the behavior of the provided `pyfiglet` project.

## Repository

The original project is available in:

`/workspace/repo/pyfiglet/`

It is pinned to a specific upstream commit. Its standard FIGlet fonts are available in:

`/workspace/repo/pyfiglet/pyfiglet/fonts/`

Use these fonts as the source of truth.

## Your implementation

Implement the program in Go in the repository root:

`/workspace/repo/`

The program must build as:

```bash
go build -o /tmp/figlet .
```

Use Go's standard library only. Do not require Python or external runtime dependencies.

Your implementation must work when invoked from any current working directory. Resolve bundled fonts reliably rather than assuming the caller is running the program from the repository root.

## Command-line interface

Support the following options:

| Option | Required behavior |
|---|---|
| `-f FONT` | Select the font |
| `-w COLS` | Set the output width |
| `-j auto\|left\|center\|right` | Set justification |
| `-D auto\|left-to-right\|right-to-left` | Set print direction |
| `-r` | Select a random font |
| `-F` | Flip the rendered output |
| `-s` | Use smushing mode |
| `-n` | Disable smushing |

Accept the input text as positional command-line arguments.

## Compatibility requirements

- Match the reference program's rendered output byte-for-byte.
- Respect font-specific character layouts, glyph dimensions, comments, and header settings.
- Implement the applicable FIGlet layout and smushing behavior, including character-specific smushing rules.
- Handle kerning and horizontal fitting correctly.
- Support text wrapping according to the requested width.
- Respect justification and print direction.
- Handle the interaction between command-line flags and font defaults correctly.
- Support the standard fonts supplied with the repository.
- Handle punctuation, whitespace, multiline text, and characters that may not exist in a selected font.

Do not assume that every font uses the same layout rules.

## Scope

Implement only these options:

`-f`, `-w`, `-j`, `-D`, `-r`, `-F`, `-s`, and `-n`.

Options `-c`, `-L`, `-l`, and `-i` are outside the scope of this task.

## Quality requirements

- Organize the implementation into clear, maintainable Go code.
- Handle malformed or missing font files safely.
- Avoid hardcoding expected output strings.
- Do not depend on the reference Python implementation at runtime.
- Ensure `go build ./...` succeeds.
