# NOTES: pyfiglet / figlet-go

Author notes and technical reference for `pyfiglet` and the `figlet-go` Harbor task.

---

## 1. Source & Licence

| Field | Value |
|---|---|
| **Repository** | https://github.com/pwaller/pyfiglet |
| **Commit SHA** | `255827efbc09d662875dad50fa0edc1e1263bf45` |
| **Commit Date** | `2026-08-02T22:51:18+01:00` |
| **Version** | `1.0.4` (from `pyfiglet/version.py`) |
| **Licence** | **MIT License (MIT)** (from `LICENSE`, `setup.py`, and `pyfiglet/__init__.py`) |

---

## 2. Why `python -m pyfiglet hello` Fails Straight After Cloning & The Makefile Fix

### Why it fails:
In a freshly cloned repository, font files are located in `pyfiglet/fonts-standard/` and `pyfiglet/fonts-contrib/`. The `pyfiglet/fonts/` directory does not exist.

When `python -m pyfiglet hello` runs, `FigletFont.preloadFont(DEFAULT_FONT)` in `pyfiglet/__init__.py` attempts to locate the default font (`standard.flf`) inside the package resources via:
```python
path = importlib.resources.files('pyfiglet.fonts').joinpath(fn)
```
Because `pyfiglet/fonts` is missing, `importlib` fails to resolve `pyfiglet.fonts` (`ModuleNotFoundError: No module named 'pyfiglet.fonts'`), or `preloadFont` fails to locate the font and raises `FontNotFound('standard')`. The CLI catches `FontNotFound` and prints:
```
pyfiglet error: requested font 'standard' not found.
```
and exits with code 1.

### Which Makefile step fixes it:
The `Makefile` defines the `minimal` (and `full`) targets:
```makefile
clean:
	rm -rf build/
	rm -rf pyfiglet/fonts/
	mkdir pyfiglet/fonts/

minimal: clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	python3 -m build
```
The exact step that fixes the issue is copying the standard fonts into `pyfiglet/fonts`:
```bash
cp pyfiglet/fonts-standard/* pyfiglet/fonts
```
(preceded by creating the directory: `mkdir -p pyfiglet/fonts`).

To set up the fonts manually without building wheels:
```bash
mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/
```
Once this step is completed, `python -m pyfiglet hello` (or `python -m pyfiglet -f slant "hello"`) succeeds and renders the ASCII banner.

---

## 3. Smushing Rules & Kerning

FIGlet characters (FIGcharacters) are made up of rows of ordinary text characters (sub-characters). When two FIGcharacters are placed adjacent to one another horizontally, they can be squeezed together according to the font's layout mode (`smushMode`).

In `pyfiglet/__init__.py`, the `FigletBuilder` class defines smushing constants and implements the logic in `smushChars(left, right)` and `smushAmount(buffer, curChar)`.

Overlapping only occurs if both the previous and current characters have a width of at least 2 (`self.prevCharWidth >= 2 and self.curCharWidth >= 2`).

### Kerning (`SM_KERN = 64`)
- **Rule**: Moves adjacent characters closer together until their non-blank sub-characters touch, but **never overlaps or replaces visible ink**.
- When `SM_SMUSH` (128) is not set, `smushChars()` returns `None` for all non-space characters (`if (self.font.smushMode & self.SM_SMUSH) == 0: return`).
- Whitespace sub-characters are absorbed: `' '` + `'|'` $\rightarrow$ `'|'` and `'|'` + `' '` $\rightarrow$ `'|'`.
- **Tiny Example**:
  - `' '` + `'|'` $\rightarrow$ `'|'` (whitespace is trimmed to bring glyphs together)
  - `'|'` + `'|'` $\rightarrow$ `None` (touch side-by-side as `||`, without merging)

---

### The Six Controlled Horizontal Smushing Rules

Controlled smushing is active when `SM_SMUSH` (`128`) is set and specific rule bits (`1`–`32`) are enabled:

#### Rule 1: Equal Character Smushing (`SM_EQUAL = 1`)
- **Rule**: Two identical sub-characters are smushed into a single sub-character (`left == right`).
- **Exceptions**: Does not smush hardblanks unless Rule 6 (`SM_HARDBLANK`) is also set.
- **Tiny Example**:
  - `'|'` + `'|'` $\rightarrow$ `'|'`
  - `'/'` + `'/'` $\rightarrow$ `'/'`

#### Rule 2: Underscore / Lowline Smushing (`SM_LOWLINE = 2`)
- **Rule**: An underscore (`'_'`) will be replaced by (eaten by) any of the following 12 hierarchy characters: `|`, `/`, `\`, `[`, `]`, `{`, `}`, `(`, `)`, `<`, `>`.
- **Tiny Example**:
  - `'_'` + `'|'` $\rightarrow$ `'|'`
  - `'/'` + `'_'` $\rightarrow$ `'/'`

#### Rule 3: Hierarchy Smushing (`SM_HIERARCHY = 4`)
- **Rule**: Sub-characters are classified into a 6-level hierarchy:
  1. `|` (lowest)
  2. `/`, `\`
  3. `[`, `]`
  4. `{`, `}`
  5. `(`, `)`
  6. `<`, `>` (highest)
  When two sub-characters from different classes meet, the character from the higher (latter) class wins and replaces the junction.
- **Tiny Example**:
  - `'|'` (class 1) + `'/'` (class 2) $\rightarrow$ `'/'`
  - `'/'` (class 2) + `'['` (class 3) $\rightarrow$ `'['`
  - `'['` (class 3) + `'{'` (class 4) $\rightarrow$ `'{'`
  - `'{'` (class 4) + `'('` (class 5) $\rightarrow$ `'('`
  - `'('` (class 5) + `'<'` (class 6) $\rightarrow$ `'<'`

#### Rule 4: Opposite Pair Smushing (`SM_PAIR = 8`)
- **Rule**: Smushes opposing brackets (`'['` and `']'`), braces (`'{'` and `'}'`), or parentheses (`'('` and `')'`) together, replacing the pair with a vertical bar (`'|'`).
  - `left + right` or `right + left` in `['[]', '{}', '()']` $\rightarrow$ `'|'`.
- **Tiny Example**:
  - `'['` + `']'` $\rightarrow$ `'|'` (also `']'` + `'['` $\rightarrow$ `'|'`)
  - `'{'` + `'}'` $\rightarrow$ `'|'` (also `'}'` + `'{'` $\rightarrow$ `'|'`)
  - `'('` + `')'` $\rightarrow$ `'|'` (also `')'` + `'('` $\rightarrow$ `'|'`)

#### Rule 5: Big X Smushing (`SM_BIGX = 16`)
- **Rule**: Smushes specific diagonal slashes and inward-facing angle brackets:
  - `'/'` + `'\\'` $\rightarrow$ `'|'` (slash meets backslash at the top $\rightarrow$ vertical bar)
  - `'\\'` + `'/'` $\rightarrow$ `'Y'` (backslash meets slash at the bottom $\rightarrow$ `'Y'`)
  - `'>'` + `'<'` $\rightarrow$ `'X'` (opposing angle brackets facing inward $\rightarrow$ `'X'`)
  *(Note: `'<'` + `'>'` is NOT smushed by this rule. Historically named "BIG X" because originally all three formed `'X'`)*
- **Tiny Example**:
  - `'/'` + `'\\'` $\rightarrow$ `'|'`
  - `'\\'` + `'/'` $\rightarrow$ `'Y'`
  - `'>'` + `'<'` $\rightarrow$ `'X'`

#### Rule 6: Hardblank Smushing (`SM_HARDBLANK = 32`)
- **Rule**: Smushes two hardblank characters together into a single hardblank. Hardblanks prevent smushing with any other character; only two identical hardblanks merge.
- **Tiny Example**:
  - `'$'` + `'$'` $\rightarrow$ `'$'` (where `'$'` is the font's defined hardblank)

---

### Universal Smushing (Universal Overlapping)
- **Rule**: When smushing is requested (`SM_SMUSH = 128`), but no controlled smushing rules are enabled (`(smushMode & 63) == 0`), universal overlapping occurs:
  - Hardblanks yield to visible sub-characters (`hardblank` + `char` $\rightarrow$ `char`).
  - Visible characters overlap based on text flow order:
    - In `left-to-right`: the right (later) character overrides the left (`'/'` + `'\\'` $\rightarrow$ `'\\'`).
    - In `right-to-left`: the left (later in RTL order) character overrides the right (`'/'` + `'\\'` $\rightarrow$ `'/'`).

---

## 4. Command-Line Options

| Option | Argument / Type | Default | Description |
|---|---|---|---|
| **`-f`**, `--font` | `FONT` (string) | `standard` | Specifies the font file (`.flf` or `.tlf`) to render the text with. Loads from the package fonts directory or search path. |
| **`-w`**, `--width` | `COLS` (integer) | `80` | Sets the output terminal width in columns for line wrapping and justification. If rendered text exceeds this column width, FIGlet wraps to a new line (breaking on spaces when possible). Also serves as the line width for `-j center` and `-j right`. |
| **`-j`**, `--justify` | `SIDE` (`auto` \| `left` \| `center` \| `right`) | `auto` | Sets text justification/alignment across the given `-w` width: <br>• `auto`: Aligns to print direction (`left` for LTR, `right` for RTL).<br>• `left`: Left-aligns output (no extra leading padding).<br>• `center`: Centers each line by prepending `(width - line_length) // 2` spaces.<br>• `right`: Right-aligns each line by prepending `width - line_length - 1` spaces. |
| **`-D`**, `--direction` | `DIRECTION` (`auto` \| `left-to-right` \| `right-to-left`) | `auto` | Sets the direction text is formatted in:<br>• `auto`: Uses the font's header `printDirection` (0 for LTR, 1 for RTL).<br>• `left-to-right`: Formats text from left to right.<br>• `right-to-left`: Formats text from right to left; adjusts smushing dominance so foreground text stays in front. |
| **`-r`**, `--reverse` | Flag (`store_true`) | `False` | Renders a horizontal mirror image of the output text. Reverses character order on each row and translates glyph sub-characters via `__reverse_map__` (e.g. `/` $\leftrightarrow$ `\`, `[` $\leftrightarrow$ `]`, `(` $\leftrightarrow$ `)`, `<` $\leftrightarrow$ `>`). |
| **`-F`**, `--flip` | Flag (`store_true`) | `False` | Inverts/flips the rendered output text vertically upside down. Reverses row order and translates glyph sub-characters via `__flip_map__` (e.g. `_` $\leftrightarrow$ `-`, `^` $\leftrightarrow$ `v`, `/` $\leftrightarrow$ `\`). |
| **`-s`**, `--strip-surrounding-newlines` | Flag (`store_true`) | `False` | Strips all empty leading lines before the text and all empty trailing lines after the rendered text, while preserving leading indentation on the first non-empty line and empty lines between rendered characters. |
| **`-n`**, `--normalize-surrounding-newlines` | Flag (`store_true`) | `False` | Normalizes surrounding newlines so that output has exactly one empty newline line before and one empty newline line after the rendered text (`'\n' + strip_surrounding_newlines() + '\n'`). Note: if `-s` is also supplied, `-s` takes precedence in `pyfiglet`. |
