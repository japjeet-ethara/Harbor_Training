# pyfiglet notes

| | |
|---|---|
| Repository | https://github.com/pwaller/pyfiglet |
| Commit | `255827efbc09d662875dad50fa0edc1e1263bf45` |
| Commit date | `2026-08-02T22:51:18+01:00` |
| Licence | MIT (`LICENSE`, "The MIT License (MIT)", Christopher Jones, Stefano Rivera, Peter Waller and contributors) |
| Code | `pyfiglet/__init__.py` (1048 lines): `FigletFont` parses fonts, `FigletBuilder` renders, `FigletString` mirrors/flips/strips, `main()` is the CLI |

All examples below were produced by running the original code (Python 3.12.0), not written from memory.

## Why `python -m pyfiglet hello` fails straight after cloning

`FigletFont.preloadFont` loads fonts with `importlib.resources.files('pyfiglet.fonts')`, but the repository has no `pyfiglet/fonts/` folder. The fonts ship in `pyfiglet/fonts-standard/` (and `pyfiglet/fonts-contrib/`). The `Makefile` fixes this: `clean` recreates an empty `pyfiglet/fonts/`, then `minimal` runs `cp pyfiglet/fonts-standard/* pyfiglet/fonts`. The same step by hand:

```
mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/
python -m pyfiglet -f slant hello
```

```
    __         ____    
   / /_  ___  / / /___ 
  / __ \/ _ \/ / / __ \
 / / / /  __/ / / /_/ /
/_/ /_/\___/_/_/\____/ 
```

Only `fonts-standard/` is used (`fonts-contrib/` has fonts from many authors). The copy also brings `fonts-standard/__init__.py`, which the port must delete with the other `.py` files.

## Layout: full width, kerning, smushing

The font header's 8th field (`fullLayout`) picks the layout. If it is missing, `oldLayout` is converted: `0` gives 64, below 0 gives 0, else `(old & 31) | 128`.

| Bits | Meaning |
|---|---|
| neither 64 nor 128 | full width: letters are placed side by side (`5x7`, `term`) |
| 64, not 128 (kerning) | letters slide together until they touch; no character is merged (`banner`, `script`) |
| 128 (smushing), rules = 0 | universal smushing: the later letter's character wins, hardblanks lose (`mini`, `shadow`) |
| 128 with rule bits 1 to 32 | controlled smushing with the six rules below (`standard`, `slant`, `small`, `big`, `ivrit`) |

Before any rule: a space always gives way to the other character, and nothing merges when the previous or the current letter is less than 2 columns wide.

## The six smushing rules (`FigletBuilder.smushChars`)

| Bit | Rule | Examples (left + right → result) |
|---|---|---|
| 1 | Equal: two equal characters become one (not hardblanks) | `\|` + `\|` → `\|`; `#` + `#` → `#`; `$` + `$` → no smush |
| 2 | Underscore: `_` is replaced by any of `\|/\[]{}()<>` | `_` + `\|` → `\|`; `/` + `_` → `/`; `_` + `<` → `<` |
| 4 | Hierarchy: classes `\|` < `/\` < `[]` < `{}` < `()` < `<>`; the higher class wins | `\|` + `/` → `/`; `\` + `[` → `[`; `{` + `]` → `{`; `<` + `)` → `<` |
| 8 | Opposite pair: `[]`, `{}`, `()` in either order become `\|` | `[` + `]` → `\|`; `}` + `{` → `\|`; `(` + `)` → `\|` |
| 16 | Big X | `/` + `\` → `\|` (not `X`, despite the name), `\` + `/` → `Y`, `>` + `<` → `X`, `<` + `>` → no smush |
| 32 | Hardblank: two hardblanks become one | `$` + `$` → `$`; `$` + `a` → no smush |
| 64 | Kerning (not a smush) | `\|` + `\|` → no smush; letters only touch |
| (0) | Universal (rules = 0) | `a` + `b` → `b`; `$` + `b` → `b`; `a` + `$` → `a`; right-to-left `a` + `b` → `a` |

Rendered pairs in `standard` (rules 1+2+4+8), right edge marked with `|`:

```
-f standard "[]"        -f standard "_|"          -f standard "ll"
 __ __ |                       _ |                 _ _ |
| _|_ ||                      | ||                | | ||
| | | ||                      | ||                | | ||
| | | ||                      | ||                | | ||
|__|__||                 _____| ||                |_|_||
                        |_____|_||                     |
```

How much two letters overlap (`smushAmount`) is the minimum over all rows of: the gap between the last non-space of the left row and the first non-space of the right row, plus 1 when the two edge characters can merge. Only ASCII spaces count as gap.

## Rare cases (where a port goes wrong)

1. No shipped font sets bit 16 or bit 32, so Big X and hardblank smushing never run. The used rule sets are 15, 1 (`digital`) and 0. Likewise, no glyph in the tested fonts is narrower than 2 columns, so the "width below 2" guard never fires. A search over every pair of printable ASCII characters also found no input where these change the output: the `{}` versus `()<>` hierarchy step (no glyph edges of those classes ever meet), and which side wins in universal smushing right-to-left. A port that gets any of these wrong still passes; no input can tell.
2. Right-to-left swaps the roles: the new letter is the left side, the line so far is the right side, and with universal smushing the left character wins.
3. `-j auto` means `right` for a right-to-left font (`ivrit` has print direction 1). `-j right` pads with `width - len(row) - 1` spaces, `center` with `int((width - len(row)) / 2)`; both use `-w`, not the terminal width.
4. Wrapping: a letter that makes the line `>= width` (not `>`) ends the line. The line breaks at the last space; the space itself is dropped. With no space, the line breaks before the letter.
5. After a wrap `prevCharWidth` is set to the width of the letter that did not fit, not 0, which changes the next smush.
6. The last line is printed only if its first row is not empty.
7. A newline in the text ends the line like a space would; `"\n"` alone prints a block of empty rows.
8. Characters missing from the font are skipped silently (`€`, `日本`, tab).
9. `-s` wins over `-n`. Order is reverse, then flip, then strip/normalize. `-s` ends with `rstrip()`, so the output loses its last newline before `main()` adds one.
10. `-r` swaps `()`, `/\`, `<>`, `[]`, `{}` then reverses each row. `-F` reverses the row order and maps `/`↔`\`, `A`↔`V`, `M`↔`W`, `P`→`b`, `R`→`b`, `b`→`P`, `m`↔`w`, `^`↔`v`, `_`→`-`.
11. Font parsing: the file is decoded as UTF-8 with `replace`; the end mark of a glyph is the last non-space character of its first row; `{1,2}` copies of it and trailing spaces are cut from every row; `bubble`, `digital` and `term` use `\x7f` as hardblank.
12. pyfiglet crashes on `width < letter width` and loops forever when a letter fills the whole width on an empty line. Those command lines are excluded from the cases.

## The options in scope

| Option | Effect |
|---|---|
| `-f FONT` | font name (default `standard`) |
| `-w COLS` | width for wrapping and justification (default 80) |
| `-j auto\|left\|center\|right` | justification; `auto` = `left`, or `right` for right-to-left |
| `-D auto\|left-to-right\|right-to-left` | direction; `auto` uses the font header (1 = right-to-left) |
| `-r` | mirror image |
| `-F` | flip upside down |
| `-s` | remove empty lines before and after |
| `-n` | exactly one empty line before and after |

Out of scope: `-c` (colour), `-L` (install font), `-l` (list fonts), `-i` (font info).
