# Source study

Repository: https://github.com/pwaller/pyfiglet

Pinned SHA: `255827efbc09d662875dad50fa0edc1e1263bf45`

Commit timestamp: `2026-08-02T22:51:18+01:00` (read from git log).

Implementation license: MIT; the original notice is preserved in LICENSE.pyfiglet. Only fonts-standard is used; fonts-contrib is excluded. Font files retain their own upstream notices.

The checkout has fonts in pyfiglet/fonts-standard, but importlib.resources loads pyfiglet/fonts. The Makefile's minimal target first cleans/creates that directory and copies fonts-standard/* into it. setup.py also copies this directory if absent. Perform `mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/` before running the original module.

## Smushing, in source order

ASCII space gives way to the other character. Non-space overlap is disallowed when either glyph width is less than two. Font mode bits enable individual rules:

1. Equal (1): `|` + `|` becomes `|`, except hardblanks.
2. Underscore (2): `_` + `/` becomes `/`; the other member can be any character in `|/\[]{}()<>`, in either order.
3. Hierarchy (4): classes ascend `|`, `/\`, `[]`, `{}`, `()`, `<>`; the higher class wins, e.g. `|` + `[` becomes `[`. Members of one class do not merge by this rule.
4. Opposite pair (8): `[` + `]`, `{` + `}`, `(` + `)` become `|`, in either order.
5. Big-X (16): `/` + `\` becomes `|`; `\` + `/` becomes `Y`; `>` + `<` becomes `X`. These are directional. The exercise's introductory shorthand and a source comment are misleading; the executable method is the authority.
6. Hardblank (32): two font hardblanks merge to one hardblank; it becomes an ordinary space only after rendering. Hardblank with another non-space character cannot merge in controlled smushing.

Kerning (64) removes only separating ASCII spaces until ink touches, without merging ink. Smushing (128) additionally permits merges. Smushing with no low six rule bits uses universal overlap: the later input glyph dominates, even when rendering right-to-left, with visible characters preferred to hardblanks.

## Options

- `-f FONT`: font, default standard.
- `-w COLS`: width, default 80; wrapping occurs when the new width is greater than or equal to COLS. Right justification pads by COLS minus row length minus one; center truncates half the difference.
- `-j auto|left|center|right`: alignment using the supplied width. Auto follows resolved direction.
- `-D auto|left-to-right|right-to-left`: glyph placement direction; auto follows the font header, defaulting to left-to-right.
- `-r`: mirrors each rendered row and translates directional artwork characters.
- `-F`: reverses the rendered row order and translates vertically oriented characters; applied after reverse.
- `-s`: removes blank leading rows and trailing whitespace, preserving internal blank rows; takes precedence over -n.
- `-n`: normalizes surrounding newlines. The CLI always appends another final newline after transformation.

Text arguments are joined with spaces. Missing glyphs are skipped, including unsupported Unicode. An explicit newline flushes the current line. Wrapping prefers the last recorded space and resumes after it.

## Rare cases and implementation pitfalls

`|_|`, `/\`, `\/`, `><`, `[]{}()<>`, hardblanks, double spaces, leading/trailing spaces, explicit newlines, tabs, empty strings, missing glyphs, `é ß ñ`, right-to-left at widths 10 and 20, center with width 40, and combined reverse/flip/strip/normalize.

Upstream has no finite answer when a first glyph is exactly as wide as the available width: the wrap logic retries it forever. Wider glyphs raise CharNotPrinted. The generator excludes both situations, rather than inventing outputs or changing the original. It still samples every requested width.
