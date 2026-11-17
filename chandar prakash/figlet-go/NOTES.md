# pyfiglet Analysis & Reference Notes

## Repository Information
- **URL**: https://github.com/pwaller/pyfiglet
- **Pinned Commit SHA**: 255827efbc09d662875dad50fa0edc1e1263bf45
- **Commit Date**: 2026-08-02T22:51:18+01:00
- **License**: MIT License (MIT)

## Running from a Fresh Clone & Font Setup Step
Running `python -m pyfiglet hello` fails immediately after cloning because the default `standard` font is expected in `pyfiglet/fonts/`, but fresh clones store fonts in `pyfiglet/fonts-standard/`. The `Makefile` targets (`minimal` or `full`) fix this by creating the directory and copying standard fonts.

Setup step required:
```sh
mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/
```

## Smushing and Kerning Rules

When two FIGlet characters touch, smushing rules determine how overlapping edge characters merge. A font's layout flags (smushMode) control which rules are enabled.

`H` denotes the font's hardblank character (often `$`).

| Rule | Flag / Bit | Description | Example Input | Result |
| --- | --- | --- | --- | --- |
| 1. Equal Character | SM_EQUAL (1) | Two identical non-hardblank characters smush into that character | `A` + `A` | `A` |
| 2. Underscore | SM_LOWLINE (2) | `_` smushes with any character in hierarchy: `\|/\[]{}()<>` | `_` + `\|` | `\|` |
| 3. Hierarchy | SM_HIERARCHY (4) | Characters in classes smush into the higher-ranked class. Classes from low to high: `\|`, `/\`, `[]`, `{}`, `()`, `<>`. | `\|` + `/` | `/` |
| 4. Matched Pair | SM_PAIR (8) | Matched brackets smush into `\|`: `[]` or `][` -> `\|`, `{}` or `}{` -> `\|`, `()` or `)(` -> `\|` | `[` + `]` | `\|` |
| 5. Big X | SM_BIGX (16) | `/` + `\` -> `\|`, `\` + `/` -> `Y`, `>` + `<` -> `X` | `>` + `<` | `X` |
| 6. Hardblank | SM_HARDBLANK (32) | Two hardblanks smush into one hardblank | `$` + `$` | `$` |
| Universal Smushing | SM_SMUSH (128) & ~63 | If smush is enabled but no specific rule 1-6 applies, the latter character in reading order wins | `A` + `B` | `B` |
| Kerning | SM_KERN (64) | Glyphs move closer until whitespace borders touch without overlapping non-space glyphs | `A ` + ` B` | `AB` |

## Hierarchy Classes (Rule 3)
1. `|` (rank 1)
2. `\` and `/` (rank 2)
3. `[` and `]` (rank 3)
4. `{` and `}` (rank 4)
5. `(` and `)` (rank 5)
6. `<` and `>` (rank 6)

When two characters from different classes touch, the higher-ranked character wins.

## Big X Rules (Rule 5)
- `/` (left) + `\` (right) -> `|`
- `\` (left) + `/` (right) -> `Y`
- `>` (left) + `<` (right) -> `X` (Note: `<` + `>` does not smush under Big X)

## Command-Line Options
- `-f FONT`: Render using specified font (default: `standard`).
- `-w COLS`: Terminal width in columns for line wrapping and justification (default: `80`).
- `-j SIDE`: Justification side: `auto`, `left`, `center`, `right`. `auto` defaults to print direction (`left` for left-to-right, `right` for right-to-left).
- `-D DIRECTION`: Print direction: `auto`, `left-to-right`, `right-to-left`. `auto` uses font's header printDirection (0: left-to-right, 1: right-to-left).
- `-r`: Mirror the rendered output horizontally (reverses character order and inverts symmetric characters like `/` <-> `\`, `(` <-> `)`).
- `-F`: Flip the rendered output vertically (inverts lines vertically and inverts symmetric characters like `^` <-> `v`).
- `-s`: Strip empty leading and trailing lines around rendered output.
- `-n`: Normalize surrounding newlines to exactly one newline before and after rendered output (overridden by `-s` if both present).
