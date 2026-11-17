# NOTES: pyfiglet, the source of this task

Author of the task: sugandhsharma.

## 1. Source

- Repository: https://github.com/pwaller/pyfiglet
- SHA: `255827efbc09d662875dad50fa0edc1e1263bf45`
- Commit date: `2026-08-02T22:51:18+01:00`
- Package version: 1.0.4 (`pyfiglet/version.py`)
- Code read: `pyfiglet/__init__.py` (1048 lines; the classes `FigletFont`, `FigletString`, `FigletBuilder`,
  `Figlet` and the function `main`), `Makefile`, `setup.py`, `LICENSE`.

## 2. Licence

MIT. File `LICENSE`: "The MIT License (MIT)", "Copyright (c) 2007-2018 Christopher Jones, Stefano Rivera,
Peter Waller, and various contributors". MIT is one of the licences allowed for this exercise.
Only the fonts of `pyfiglet/fonts-standard/` are used. The fonts of `fonts-contrib/` come from many authors
and are removed from the image.

## 3. Why `python -m pyfiglet hello` fails straight after cloning

It stops with `ModuleNotFoundError: No module named 'pyfiglet.fonts'`.
The code loads a font with `importlib.resources.files('pyfiglet.fonts')`, so it needs a folder
`pyfiglet/fonts`. The repository does not have that folder: the fonts are kept in `pyfiglet/fonts-standard/`
(and `pyfiglet/fonts-contrib/`).

The project's own `Makefile` makes the folder. The target `clean` runs `rm -rf pyfiglet/fonts/` and
`mkdir pyfiglet/fonts/`; the target `minimal` then runs `cp pyfiglet/fonts-standard/* pyfiglet/fonts`
(the target `full` also copies `fonts-contrib`). Stage 1 of the Dockerfile does the `minimal` step:

```
mkdir pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/
```

After that `python -m pyfiglet -f slant "hello"` draws the slanted letters. The folder then holds 72 files:
67 fonts (`.flf`), 4 control files (`.flc`) and one `__init__.py`.

## 4. The smushing rules

When a letter is added, the program first works out how many columns it may move into the line
(`smushAmount`), then merges the columns that overlap (`smushChars`). A blank always gives way to the other
character. Where two visible characters meet, the font's layout number decides. Every result below was
returned by `FigletBuilder.smushChars` of the original.

| Rule | Layout bit | What it does | Two characters and the result |
|---|---|---|---|
| 1. Equal character | 1 | two equal characters become one (not hardblanks) | `|` + `|` -> `|`, `/` + `/` -> `/` |
| 2. Underscore | 2 | `_` is replaced by any of `| / \ [ ] { } ( ) < >` | `_` + `/` -> `/`, `|` + `_` -> `|` |
| 3. Hierarchy | 4 | classes `|`, `/\`, `[]`, `{}`, `()`, `<>`: the later class wins | `|` + `/` -> `/`, `/` + `[` -> `[`, `]` + `{` -> `{`, `}` + `(` -> `(`, `)` + `<` -> `<` |
| 4. Opposite pair | 8 | opposing brackets become a bar | `[` + `]` -> `|`, `}` + `{` -> `|`, `(` + `)` -> `|` |
| 5. Big X | 16 | slashes and angle brackets that meet | `/` + `\` -> `|`, `\` + `/` -> `Y`, `>` + `<` -> `X` |
| 6. Hardblank | 32 | two hardblanks become one hardblank | `$` + `$` -> `$` |
| Kerning | 64 | letters move together until they touch; no column is shared | `|` + `|` -> not merged |
| Universal smushing | 128 with none of bits 1 to 32 | the later letter of the text wins the column; a hardblank loses | `a` + `b` -> `b` (left-to-right), `a` + `b` -> `a` (right-to-left) |

Three more facts decide many lines:

- A letter that is less than 2 columns wide never shares a column, and nothing shares a column with it
  (`prevCharWidth < 2 or curCharWidth < 2`).
- A hardblank (`$` in these fonts) meets nothing except under rule 6; it is printed as a space at the end.
- The first letter of a line loses the blank columns that all its rows start with, because the empty line
  counts as blank.

The layout numbers of the eight fonts the cases use:

| Font | Height | Layout | Meaning |
|---|---|---|---|
| standard, big | 6, 8 | 24463 | smushing with rules 1, 2, 3, 4 |
| slant | 6 | 18319 | smushing with rules 1, 2, 3, 4 |
| small | 5 | 22415 | smushing with rules 1, 2, 3, 4 |
| mini | 4 | 1920 | universal smushing |
| shadow | 5 | 4992 | universal smushing |
| banner | 8 | 64 | kerning |
| script | 7 | 3904 | kerning |

None of the eight fonts, and none of the 67 standard fonts, switches on rule 5 or rule 6, so no case can
check rules 5 and 6. None of the eight has a letter narrower than 2 columns, so the narrow-letter rule
decides no case either. None of the eight is a right-to-left font.

Two more standard fonts are therefore used in about one case in seven:

| Font | Height | Layout | Why it is in the cases |
|---|---|---|---|
| term | 1 | 0 (full width) | it prints every character as itself, so `-F` and `-r` meet all the characters their tables change; the eight fonts draw with only about 20 different characters |
| ivrit | 6 | 16271, direction 1 | the only standard font whose header says right-to-left, which is what `-D auto` and `-j auto` read |

## 5. The eight options

| Option | What the original does |
|---|---|
| `-f FONT` | loads `FONT.tlf`, else `FONT.flf`, from the fonts folder; default `standard` |
| `-w COLS` | the width. A letter is put on a new line when the line would reach `COLS` columns or more, so a line is at most `COLS - 1` wide; the line is cut at the last blank if there is one. Default 80 |
| `-j auto|left|center|right` | `left`: nothing is added. `center`: `int((COLS - length) / 2)` spaces in front of each row. `right`: `COLS - length - 1` spaces in front of each row. `auto`: `left` for left-to-right, `right` for right-to-left. `COLS` is the value of `-w`, not 80 |
| `-D auto|left-to-right|right-to-left` | right-to-left puts each new letter in front of the line. `auto` takes the direction from the font header |
| `-r` | every row is mirrored, and `( )`, `/ \`, `< >`, `[ ]`, `{ }` are swapped |
| `-F` | the rows are put in the opposite order, and some characters are swapped: `/ \`, `A V`, `M W`, `^ v`, `m w`, `_` becomes `-`, `P` and `R` become `b`, `b` becomes `P` |
| `-s` | empty rows before the first drawn row are dropped, then all whitespace at the very end is removed |
| `-n` | the same as `-s`, with one newline in front and one after. If `-s` is also given, `-s` wins |

The order is fixed: render, then `-r`, then `-F`, then `-s` or `-n`, then one final newline.

## 6. Rare cases

Found while reading the code and by running the original. These are what the cases aim at.

- Extra letters: after the 95 ASCII letters a font file holds 7 German letters, and then letters with a code
  line. Only code lines that start with `0x` are loaded. So `standard` draws `ß` but skips `é` and `ñ`
  (their code lines are decimal), while it does draw `ā` (`0x0101`). A letter the font does not have is
  skipped without a gap.
- A letter wider than the window stops the original with an error. A letter exactly as wide as the window
  makes it loop for ever. Both are left out of the cases (`tests/gen.py`).
- `-w 20 -j center` centres in 20 columns, and `-j right` leaves one spare column at the right edge.
- With `-D right-to-left` and no `-j`, the rows are pushed to the right edge.
- A line break in the text ends the block of rows, also when the block is empty.
- The flip table is not symmetric (`P -> b`, `R -> b`, `b -> P`).
- Rule 5 in this code is not the usual "X": `/` + `\` gives `|` and `\` + `/` gives `Y`.
- Three standard fonts (`bubble`, `digital`, `term`) are not valid UTF-8. The original reads them with
  "replace", so each faulty byte sequence becomes one U+FFFD.

## 7. Rules the agent got wrong, and the Docker traps

Honest record of this build.

- The squeezing rules were right at the first full comparison: 2000 of 2000 visible cases, 2000 of 2000
  hidden cases, and 40,000 of 40,000 extra cases over all 67 standard fonts and twelve widths
  (`dev/fuzz.py`) gave the same bytes as the original. What made that possible: the port follows
  `FigletBuilder` line by line (same order, same variables), works on characters and not on bytes, and has
  small helpers that behave like the Python string functions the original uses.
- The rule that needed the most care is the amount of overlap in right-to-left mode together with `-j`:
  both add spaces on the left, but one is part of rendering and the other is added afterwards. In the test of
  the tests (section 8) the variants that mix them up are the ones the cases must catch.
- Docker traps met while building the room:
  1. The Debian Go image (`golang:1.23`) contains `/usr/bin/python3` and git, so it cannot be the room.
  2. The Alpine Go image has no `bash`, and Harbor runs its commands with bash, so the Dockerfile adds it.
  3. `harbor task init` of Harbor 0.25.0 writes `environment_mode = "separate"` and a `tests/Dockerfile`
     (a Python image). This task uses the shared verifier, so the setting is `"shared"`, that file is
     removed, and the grader is a Go program that runs in the room itself. `harbor lint` then gives the one
     expected warning, `shared-verifier`.
  4. The build can only see `environment/`, so stage 1 fetches pyfiglet from GitHub at the pinned commit.

## 8. How the tests were tested

- `python tests/gen.py` twice gives identical files; each file has 2000 cases; no case is in both.
- Room checks: `player`, `/workspace/repo`, 72 font files, `NO_PYTHON`, `/bin/bash`, `CAN_WRITE`; also no git;
  both images are pinned by digest.
- Harbor 0.25.0: oracle 1.0 with the secret drawn, do-nothing 0.0, cheat 0.1667 with no secret.
- `dev/find_rare_pairs.py` asks the original which two-character texts depend on one small part of the
  smushing rules (every pair of printable characters, five fonts, both directions). 70 of them are in the
  generator. Two parts decide no drawing at all with these fonts: the hierarchy classes `[ ]` and `{ }`.
- Broken variants of the port, one small change each (`dev/mutants.py`). First set of cases (the eight fonts
  only), 76 variants: 12 were missed by the hidden cases although a larger random set caught them, all of
  them entries of the `-F` and `-r` tables. Final set (with `term`, `ivrit` and the rare pairs), 77
  variants: the hidden cases catch all 66 that change any output; the other 11 change nothing on any case
  (rules 5 and 6, the narrow-letter rule, and a few details no standard font exercises).
  The table is in `dev/mutation_report.txt`.
