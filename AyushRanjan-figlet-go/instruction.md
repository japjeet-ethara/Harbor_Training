# Harbor Practice 2: FIGlet in Go

Implement a Go command-line program that reproduces the requested rendering
behavior of the Python `pyfiglet` CLI as closely as possible. The project must
compile with:

```sh
go build ./...
```

Use only the Go standard library. Do not use or invoke Python, and do not
create `.py` files as part of the solution.

## Command-line interface

Accept text as positional arguments and join multiple arguments with one
ASCII space, as the original CLI does. Support these options and aliases:

| Short option | Long option | Behavior |
| --- | --- | --- |
| `-f FONT` | `--font=FONT` | Select a font; default is `standard`. |
| `-w COLS` | `--width=COLS` | Set width as an integer number of columns; default is `80`. The width controls wrapping and justification. |
| `-j VALUE` | `--justify=VALUE` | Accept `auto`, `left`, `center`, or `right`; default is `auto`. In auto mode, use left justification for left-to-right direction and right justification for right-to-left direction. |
| `-D VALUE` | `--direction=VALUE` | Accept `auto`, `left-to-right`, or `right-to-left`; default is `auto`. In auto mode, use the font header's print direction (`0` means left-to-right, `1` means right-to-left; other values fall back to left-to-right). |
| `-r` | `--reverse` | For each output row, translate mirrorable characters using pyfiglet's reverse map, then reverse the row's character order. |
| `-F` | `--flip` | Reverse the order of output rows and translate characters using pyfiglet's vertical flip map. |
| `-s` | `--strip-surrounding-newlines` | Remove empty rows before the first nonempty rendered row, then remove trailing whitespace and newlines from the rendered result. Empty rows within the rendered text are retained. |
| `-n` | `--normalize-surrounding-newlines` | Strip surrounding newlines as `-s` does, then add one newline before and after the result. If both `-s` and `-n` are supplied, `-s` takes precedence. |

The original CLI applies `-r`, then `-F`, then `-s` or `-n`. After this
processing it writes the result and one additional newline. Preserve this
ordering and newline behavior. If there are no positional text arguments,
print the command usage and return a nonzero status, as the original does for
the rendering path.

Reject values outside the listed choices for `-j` and `-D`, and reject a
non-integer `-w` value. Report a clear error when the requested font cannot be
found.

## Fonts and file locations

Use the bundled standard `.flf` fonts prepared under `pyfiglet/fonts/`. Do not
depend on fonts installed elsewhere or on network access at runtime. Font
loading must work regardless of the process's current working directory.
Embed the font files in the Go program or resolve their location reliably
from the installed program; do not assume the user launched it from the
repository root.

## Rendering behavior

Parse FIGlet font headers and glyph data and render text using each font's
layout settings. Preserve pyfiglet's kerning and font-declared smushing rules,
print direction, width handling, and justification. Keep output spacing, line
breaks, character substitutions, and trailing newlines as close to the
original CLI as possible.

Keep the implementation in Go project files and use the Go standard library
only. Do not add Python files or require a Python runtime.
