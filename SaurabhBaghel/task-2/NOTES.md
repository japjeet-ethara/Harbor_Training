# PyFiglet Investigation and Specification Notes

## 1. Repository & Commit Info
- **Repository URL**: `https://github.com/pwaller/pyfiglet`
- **Pinned Commit SHA**: `255827efbc09d662875dad50fa0edc1e1263bf45`
- **Commit Date**: `2026-08-02T22:51:18+01:00`
- **License**: MIT License (`LICENSE` file)

## 2. Font Setup & Post-Clone Failure
- **Why `python -m pyfiglet hello` fails directly after cloning**:
  The repository stores font files in `pyfiglet/fonts-standard/` (and `fonts-contrib/`), but pyfiglet's font loader (`FigletFont.preloadFont`) searches under the package directory `pyfiglet/fonts/`. Straight after cloning, `pyfiglet/fonts/` does not exist or is empty, raising `FontNotFound: 'standard'`.
- **Makefile step that fixes it**:
  `make minimal` (which runs `clean` then `cp pyfiglet/fonts-standard/* pyfiglet/fonts`) or manual setup:
  ```bash
  mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/
  ```

## 3. Smushing Rules & Kerning
FIGlet combines characters by bringing them horizontally closer until sub-characters meet ("kerning") or overlap according to smushing rules ("smushing").

Constants from FIGlet:
- `SM_EQUAL` = 1
- `SM_LOWLINE` = 2
- `SM_HIERARCHY` = 4
- `SM_PAIR` = 8
- `SM_BIGX` = 16
- `SM_HARDBLANK` = 32
- `SM_KERN` = 64
- `SM_SMUSH` = 128

### The Six Smushing Rules:
1. **Rule 1: Equal characters (`SM_EQUAL` = 1)**
   Smushes two identical characters together (neither being hardblank).
   *Example*: `'|'` + `'|'` -> `'|'`.
2. **Rule 2: Lowline / Underscore (`SM_LOWLINE` = 2)**
   Smushes `'_'` with any character in `'|/\[]{}()<>'`. The non-underscore character wins.
   *Example*: `'_'` + `'/'` -> `'/'`.
3. **Rule 3: Hierarchy (`SM_HIERARCHY` = 4)**
   Smushes characters according to 6 hierarchy classes:
   Class 1: `'|'`
   Class 2: `'/\'`
   Class 3: `'[]'`
   Class 4: `'{}'`
   Class 5: `'()'`
   Class 6: `'<>'`
   When characters from two different classes meet, the higher-class character replaces the lower-class one.
   *Example*: `'/'` (class 2) + `'['` (class 3) -> `'['`.
4. **Rule 4: Opposite Pair (`SM_PAIR` = 8)**
   Opposite pairs of brackets smush into a vertical bar:
   `'['` + `']'` -> `'|'` (or `']'` + `'['` -> `'|'`)
   `'{'` + `'}'` -> `'|'` (or `'}'` + `'{'` -> `'|'`)
   `'('` + `')'` -> `'|'` (or `')'` + `'('` -> `'|'`)
   *Example*: `'['` + `']'` -> `'|'`.
5. **Rule 5: Big X (`SM_BIGX` = 16)**
   Smushes slashes and angle brackets:
   `'/'` + `'\'` -> `'|'`
   `'\'` + `'/'` -> `'Y'`
   `'>'` + `'<'` -> `'X'`
   *Example*: `'/'` + `'\'` -> `'|'`, `'>'` + `'<'` -> `'X'`.
6. **Rule 6: Hardblank (`SM_HARDBLANK` = 32)**
   Smushes two hardblanks together into a single hardblank.
   *Example*: `'$'` + `'$'` -> `'$'`.

### Universal Overlapping & Kerning:
- **Universal Overlapping** (`smushMode & 63 == 0` when `SM_SMUSH` is enabled):
  Characters overlap without rule restriction. Hardblanks yield to visible characters. Otherwise, the dominant character is the latter character in text order (in RTL: left character; in LTR: right character).
- **Kerning** (`SM_KERN` = 64):
  Characters are shifted closer until their bounding boxes touch, with zero character overlap.

## 4. Supported Command-Line Options
- `-f FONT`: Selects FIGlet font (e.g. `standard`, `slant`, `small`, `big`, `mini`, `banner`, `shadow`, `script`).
- `-w COLS`: Terminal column width for line breaking and justification (default 80).
- `-j SIDE`: Justification: `auto`, `left`, `center`, `right`. In `auto`, defaults to print direction (`left` for LTR, `right` for RTL).
- `-D DIRECTION`: Print direction: `auto`, `left-to-right`, `right-to-left`. In `auto`, defaults to font default.
- `-r`: Reverse / mirror output horizontally (with ASCII mirror character translations, e.g. `/` <-> `\`, `(` <-> `)`).
- `-F`: Flip output vertically (with upside-down character translations, e.g. `^` <-> `v`, `M` <-> `W`).
- `-s`: Strip surrounding leading and trailing empty lines from output.
- `-n`: Normalize surrounding newlines to exactly one empty line before and after.

## 5. Tricky and Rare Cases
- Smushing combinations: `|_|`, `\/`, `/\`, `<>`, `><`, `{}`, `[]`, `()`, `_/_`, `\_/`.
- Narrow column widths (`-w 10`, `-w 20`, `-w 40`) forcing aggressive wrapping and word-breaking.
- Consecutive spaces, leading/trailing whitespace, and empty lines.
- Right-to-left printing (`-D right-to-left`) interacting with smushing and `-j right` or `-j center`.
- Latin-1 characters (`é`, `ß`, `ñ`, `ä`, `ö`, `ü`, `Ä`, `Ö`, `Ü`).
- Missing glyphs in font (omitted from output without error).
