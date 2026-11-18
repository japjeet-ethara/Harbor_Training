# FIGlet Go Port

## What the repository is

This repository contains a checkout of [pyfiglet](https://github.com/pwaller/pyfiglet) at commit `255827efbc09d662875dad50fa0edc1e1263bf45`. pyfiglet is an MIT-licensed Python implementation of FIGlet: it takes a short text string and renders it in large ASCII-art letters using `.flf` font files. It supports six smushing rules that merge adjacent characters, kerning, word wrapping, justification, right-to-left layout, horizontal mirroring, vertical flipping, and surrounding-newline control.

## What to build

Build a Go program in `/workspace/repo`. Running `go build -o /tmp/figlet .` from `/workspace/repo` must produce a command-line program that accepts the following options, followed by the text to render:

| Option | Description |
| --- | --- |
| `-f FONT` | Select the FIGlet font by name (default: `standard`). |
| `-w COLS` | Set the output width in columns (default: `80`). Justification and word wrapping use this width. |
| `-j auto\|left\|center\|right` | Justify the rendered text within the width set by `-w`. `auto` follows the effective print direction: left-to-right text is left-justified, right-to-left text is right-justified. |
| `-D auto\|left-to-right\|right-to-left` | Set the text direction. `auto` uses the direction stored in the font, falling back to left-to-right if the font does not specify one. |
| `-r` | Reverse (mirror) each output line horizontally. |
| `-F` | Flip the output vertically (reverse line order). |
| `-s` | Strip empty leading and trailing lines from the output. |
| `-n` | Normalize surrounding newlines: ensure exactly one empty line before and after the rendered text. If both `-s` and `-n` are given, `-s` takes precedence. |

The program must print the same output as `python -m pyfiglet` with the same arguments, **byte for byte**.

## Fonts

The `.flf` font files in the repository may be moved to a different directory within the repository, but they must remain inside the repository tree. The program must locate its fonts relative to itself or its embedded data, and must work correctly regardless of the current working directory.

## Hard rules

- Use only the Go standard library. No third-party modules.
- No `.py` files may exist anywhere in the repository when grading runs.
- `go build ./...` must succeed with no errors.

## Not checked

Speed, memory usage, error messages, and the options `-c`, `-L`, `-l`, and `-i` are not checked.

## Grading

Grading uses hidden automatic test cases and awards a partial score.
