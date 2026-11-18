# NOTES: pyfiglet

- Repository: https://github.com/pwaller/pyfiglet
- Commit SHA: 255827efbc09d662875dad50fa0edc1e1263bf45
- Commit date: 2026-08-02T22:51:18+01:00
- Licence: MIT (`LICENSE`), allowed for the task
- All rendering logic is in `pyfiglet/__init__.py`: `FigletFont` (reads `.flf`
  files), `FigletBuilder` (smushing, wrapping, justification), `FigletString`
  (`-r` / `-F` / `-s` / `-n`) and `main()` (command-line options).

## Why `python -m pyfiglet hello` fails straight after cloning

The code loads fonts with `importlib.resources.files('pyfiglet.fonts')`, but
the repository keeps them in `pyfiglet/fonts-standard/` (and `fonts-contrib/`).
There is no `pyfiglet/fonts/` folder, so every font raises `FontNotFound`. The
`Makefile` fixes this in its `clean` + `minimal` targets:

```
rm -rf pyfiglet/fonts/ && mkdir pyfiglet/fonts/
cp pyfiglet/fonts-standard/* pyfiglet/fonts
```

Only `fonts-standard/` is used (67 `.flf` fonts plus 4 `.flc` control files, none zipped).

## How a font is chosen to smush

The font header's layout value decides which rules apply. Bit 64 means kerning,
bit 128 means smushing, and bits 1–32 are the six rules below.

| Font | smush mode | What it does |
|---|---|---|
| standard, big | 24463 | smushing with rules 1, 2, 4, 8 |
| slant, small | 18319 / 22415 | smushing with rules 1, 2, 4, 8 |
| mini, shadow | 1920 / 4992 | smushing with **no** rule bits, so "universal overlapping" |
| script | 3904 | kerning only |
| banner | 64 | kerning only |

## The six smushing rules (plus kerning)

Results come from pyfiglet's own `FigletBuilder.smushChars`. A rule only applies
when both touching letters are at least 2 columns wide.

1. **Equal characters (1):** two identical characters become one; hardblanks are excluded.
   `|`+`|` → `|`, `a`+`a` → `a`, `$`+`$` → none
2. **Underscore (2):** `_` is replaced by any of `|/\[]{}()<>`.
   `_`+`|` → `|`, `/`+`_` → `/`, `_`+`a` → none
3. **Hierarchy (4):** classes are `|` < `/\` < `[]` < `{}` < `()` < `<>`, and the higher class wins.
   `|`+`/` → `/`, `/`+`[` → `[`, `[`+`{` → `{`, `{`+`(` → `(`, `(`+`<` → `<`, `|`+`a` → none
4. **Opposite pair (8):** `[]`, `{}`, `()` in either order become `|`.
   `[`+`]` → `|`, `}`+`{` → `|`, `(`+`)` → `|`, `[`+`)` → none
5. **Big X (16):** `/`+`\` → `|`, `\`+`/` → `Y`, `>`+`<` → `X`, `<`+`>` → none.
   (pyfiglet's mapping, which differs from C figlet's.)
6. **Hardblank (32):** two hardblanks become one hardblank. `$`+`$` → `$`, `$`+`a` → none
- **Universal overlapping** (bit 128 with no rule bits): the later character wins.
  A hardblank always loses: `a`+`b` → `b`, `$`+`a` → `a`, `a`+`$` → `a`.
  In right-to-left the left one wins.
- **Kerning** (bit 64 only): letters move together until they touch but never
  overlap. Only a space can merge: ` `+`a` → `a`, `a`+`b` → none.

## The eight options in scope

| Option | Meaning |
|---|---|
| `-f FONT` | font name (default `standard`) |
| `-w COLS` | width used for wrapping and justification (default 80) |
| `-j auto\|left\|center\|right` | justification. `auto` = left for LTR, right for RTL. right adds `width - len - 1` spaces, center adds `(width - len) / 2` |
| `-D auto\|left-to-right\|right-to-left` | print direction. `auto` uses the font header (all 8 fonts are LTR) |
| `-r` | mirror every row (and swap `/\`, `()`, `[]`, `{}`, `<>`) |
| `-F` | flip upside down (reverse the row order, `/`↔`\`, `_`→`-`, `^`↔`v`, `A`↔`V`, `M`↔`W`, ...) |
| `-s` | strip empty leading and trailing lines, **and** trailing whitespace at the very end |
| `-n` | one empty line before and after (ignored if `-s` is also given) |

They're applied in this order: render, then `-r`, then `-F`, then `-s` or `-n`, then one extra `\n` is printed.

## Rare cases (things that are easy to get wrong)

- `-w 10` / `-w 20`: a letter wider than the width raises `CharNotPrinted`
  (nothing on stdout). For some widths pyfiglet even **loops forever**. These
  inputs are left out of the task.
- Wrapping goes back to the last space. The saved buffer is the one *before* the space.
- `-D right-to-left`: the new letter goes on the **left**, and the smush rules
  see (new letter, buffer) instead of (buffer, new letter).
- `-j right` adds `width - len - 1` spaces (one less than you'd expect).
  Right-to-left with `auto` also right-justifies, so both add spaces on the left.
- Characters missing from the font (`€`, `中`, tab) are silently skipped.
- Font parsing: the end marker is the last non-blank character of a letter's
  **first** row, and one or two of it are removed from every row of that letter.
  After `ÄÖÜäöüß`, extra letters are read only from lines starting with `0x`.
- `-s` uses Python's `rstrip()`, so the trailing spaces of the last row disappear too.
