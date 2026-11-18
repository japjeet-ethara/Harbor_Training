# pyfiglet — repo notes (Harbor practice 2)

## Repository facts

- URL: https://github.com/pwaller/pyfiglet
- Pinned commit: `255827efbc09d662875dad50fa0edc1e1263bf45` (short: `255827e`)
- Commit date: `2026-08-02T22:51:18+01:00`
- Licence: **MIT** (confirmed in `LICENSE` and in `setup.py`: `license='MIT'`).
- What it is: a pure-Python implementation of FIGlet. It reads `.flf`/`.tlf` font files, renders each input character as a small block of ASCII art, and joins the blocks left-to-right (or right-to-left), optionally kerning or smushing neighbouring glyphs. `FigletBuilder` in `pyfiglet/__init__.py` decides how much two glyphs may overlap, and `FigletFont` parses the font header and character table.

## Why the fresh clone fails, and the Makefile fix

The font files live in `pyfiglet/fonts-standard/`, but `FigletFont.preloadFont()` loads them through `importlib.resources.files('pyfiglet.fonts')`, i.e. from `pyfiglet/fonts/`. That directory is gitignored and does not exist in a fresh clone, so the import fails before any font is found:

```
$ python -m pyfiglet hello
ModuleNotFoundError: No module named 'pyfiglet.fonts'
```

The `minimal` (and `full`) target in the `Makefile` first runs `clean`, which creates `pyfiglet/fonts/`, then copies the standard fonts into it:

```
clean:
	rm -rf build/
	rm -rf pyfiglet/fonts/
	mkdir pyfiglet/fonts/

minimal:    clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	python3 -m build
```

The setup that actually matters (and the one used for this task):

```
mkdir -p pyfiglet/fonts
cp pyfiglet/fonts-standard/* pyfiglet/fonts/
python -m pyfiglet -f slant "hello"
```

`setup.py` also does the same copy (`shutil.copytree(fonts-standard, fonts)`) when the package is installed without `pyfiglet/fonts/`. `fonts-standard/` contains 72 font files; `fonts-contrib/` contains 521 and is not used by this task.

## The six smushing rules (plus kerning)

The rules are bit flags in the font header's `fullLayout` field, parsed into `FigletFont.smushMode`. The standard font's header is:

```
flf2a$ 6 5 16 15 46 0 24463 229
```

so its hardblank is `$`, height is 6, and `fullLayout & 255 = 143`, which enables **SM_SMUSH + equal + lowline + hierarchy + pair**. Big-X and hardblank smushing appear only in fonts whose layout enables those bits. The two-character results below were checked directly against `FigletBuilder.smushChars()`.

1. **Equal character smushing** (`SM_EQUAL = 1`): two identical non-hardblank characters become that one character.
   - Example: `|` + `|` → `|`
2. **Underscore / low-line smushing** (`SM_LOWLINE = 2`): `_` is absorbed by any of `|/\[]{}()<>`; the other character wins on either side.
   - Example: `_` + `/` → `/`
   - Example: `/` + `_` → `/`
3. **Hierarchy smushing** (`SM_HIERARCHY = 4`): six classes, lowest to highest — `|`, `/\`, `[]`, `{}`, `()`, `<>` — and the higher-class character wins.
   - Example: `|` + `/` → `/`
   - Example: `[` + `{` → `{`
4. **Opposite-pair smushing** (`SM_PAIR = 8`): `[` + `]`, `{` + `}`, and `(` + `)` become `|`. Reversed pairs do not trigger this rule.
   - Example: `[` + `]` → `|`
   - Example: `(` + `)` → `|`
5. **Big-X smushing** (`SM_BIGX = 16`): `/` + `\` → `|`; `\` + `/` → `Y`; `>` + `<` → `X`.
   - Example: `/` + `\` → `|`
   - Example: `\` + `/` → `Y`
   - Example: `>` + `<` → `X`
6. **Hardblank smushing** (`SM_HARDBLANK = 32`): two hardblanks meet as one hardblank, which the renderer later replaces with a space.
   - Example: `$` + `$` → `$` → a single space in the output
7. **Kerning** (`SM_KERN = 64`): not a smushing rule. It moves glyphs as close as possible without letting their pixels overlap.
   - Example: `|` + `/` under kerning-only → no merged character (`None`); the glyphs simply butt together.
8. **Full width** (`fullLayout & (SM_SMUSH | SM_KERN) == 0`): no kerning and no smushing; each glyph keeps its natural width.
   - Example: `|` + `/` under full-width layout → no overlap (`None`).

Additional detail that matters for an exact port:

- **Universal smushing** happens when `SM_SMUSH` is set but none of the low six rule bits are set. The visible character wins: the right character in left-to-right mode, the left character in right-to-left mode; a hardblank yields the visible character.
- `smushAmount()` decides the maximum overlap row by row. It only strips ASCII spaces, not all Unicode whitespace. It allows overlap where one edge is a space or where `smushChars()` returns a character.
- `smushChars()` refuses to overlap when either the previous or current character width is less than 2.
- In right-to-left mode, `smushAmount()` and `smushRow()` swap the left and right glyphs, so the smushing asymmetry is mirrored too.

## The eight in-scope options

The CLI is built with `optparse` in `pyfiglet/__init__.py:main()`. Only these eight options are in scope for the Go port:

1. **`-f FONT`, `--font=FONT`** — font name, default `standard`. Tries `FONT.tlf` then `FONT.flf` in `pyfiglet/fonts/`, the current directory, and the system font directories. The font header supplies height, hardblank, default print direction, and smush mode.
2. **`-D DIRECTION`, `--direction=DIRECTION`** — `auto` (default), `left-to-right`, or `right-to-left`. `auto` uses the font header's print direction: `0` → left-to-right, `1` → right-to-left, anything else → left-to-right. Right-to-left swaps glyph combination order, affects smushing preference, and makes `auto` justification become `right`.
3. **`-j SIDE`, `--justify=SIDE`** — `auto` (default), `left`, `center`, or `right`. `auto` means `left` for left-to-right and `right` for right-to-left. `right` prepends `width - len(row) - 1` spaces; `center` prepends `int((width - len(row)) / 2)` spaces; `left` prepends nothing.
4. **`-w COLS`, `--width=COLS`** — terminal width used for wrapping and justification, default `80`. When adding the next character would make the current line at least `width` columns, the builder flushes at the last recorded blank (space/newline) or, failing that, before the current character. A single glyph wider than `width` raises `CharNotPrinted`.
5. **`-r`, `--reverse`** — mirror the finished output horizontally. Each row is translated through the reverse map (`/`↔`\`, `(`↔`)`, `[`↔`]`, `{`↔`}`, `<`↔`>`, etc.) and then reversed.
6. **`-F`, `--flip`** — flip the finished output vertically. Rows are reversed and each character is translated through the flip map (`^`↔`v`, `_`↔`-`, `/`↔`\`, etc.).
7. **`-s`, `--strip-surrounding-newlines`** — remove empty lines before and after the rendered block, while keeping empty lines that occur inside it.
8. **`-n`, `--normalize-surrounding-newlines`** — output exactly one empty line before and one after the rendered block. Implemented as `'\n' + stripped_output + '\n'`. If `-s` and `-n` are both given, `-s` wins.

Out of scope (mentioned only so the port does not add them): `-c/--color`, `-L/--load`, `-l/--list_fonts`, `-i/--info_font`.

## Environment notes

- The Windows machine has the toolchain in WSL Ubuntu: Python 3.14.4, Go 1.26.8, Harbor 0.25.0, uv 0.13.7, and the Docker CLI. Docker Desktop must be running for image builds.
- The font setup above was run in WSL; `python3 -m pyfiglet -f slant hello` produced the slanted `hello` banner.
