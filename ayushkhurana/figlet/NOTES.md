# NOTES — pyfiglet (Practice Task 2: figlet-go)

Everything below was checked by running the real code, not copied from the task page.

## Source

| | |
|---|---|
| URL | https://github.com/pwaller/pyfiglet |
| Commit | `255827efbc09d662875dad50fa0edc1e1263bf45` ("Return False from isValidFont for a missing font (#161)") |
| Commit date | `2026-08-02T22:51:18+01:00` |
| Version in `pyfiglet/version.py` | 1.0.4 |
| Licence | **MIT** (`LICENSE`, "Copyright 2007-2018 Christopher Jones, Stefano Rivera, Peter Waller and contributors") |
| Code that matters | `pyfiglet/__init__.py`, 1048 lines: `FigletFont` (font loader), `FigletBuilder` (layout + smushing), `FigletString` (reverse / flip / strip), `main()` (command line) |
| Fonts | `pyfiglet/fonts-standard/` 72 files (the task uses only these), `pyfiglet/fonts-contrib/` 521 files (not used) |

## Why `python -m pyfiglet hello` fails right after cloning

Real error: `ModuleNotFoundError: No module named 'pyfiglet.fonts'`.

The code looks for fonts with `importlib.resources.files('pyfiglet.fonts')`, a folder `pyfiglet/fonts/`. The repository only has `fonts-standard/` and `fonts-contrib/`. The `Makefile` creates the missing folder:

```
clean:    rm -rf pyfiglet/fonts/ ; mkdir pyfiglet/fonts/
minimal:  clean ; cp pyfiglet/fonts-standard/* pyfiglet/fonts ; python3 -m build
```

So the fix is `mkdir -p pyfiglet/fonts && cp pyfiglet/fonts-standard/* pyfiglet/fonts/`. After that `python -m pyfiglet -f slant hello` draws slanted letters (verified).

Side effect: `fonts-standard/` contains a file `__init__.py`, so the copy puts a `.py` file inside `fonts/`. The task rule "no `.py` anywhere" therefore has to delete that one too.

## The eight options the task covers

| Option | What it does (verified) |
|---|---|
| `-f FONT` | Font name without extension. Default `standard`. Unknown font: prints `pyfiglet error: requested font 'x' not found.` on stdout, exit 1. |
| `-w COLS` | Terminal width used for wrapping and for justification. Default 80. |
| `-j auto\|left\|center\|right` | Justification. `auto` = `left` when the direction is left-to-right, `right` when it is right-to-left. `right` pads each row with `width - len(row) - 1` spaces (one less than the width). `center` pads with `int((width - len(row)) / 2)` spaces. |
| `-D auto\|left-to-right\|right-to-left` | Direction. `auto` = the font header's print-direction value (0 = left-to-right; all eight task fonts are 0). Right-to-left puts each new letter on the left and swaps the roles in the smushing rules. |
| `-r` | Mirror image: each row reversed, and `/ \ ( ) [ ] { } < >` swapped with their partners. |
| `-F` | Flip upside down: rows in reverse order, and some characters swapped for their upside-down look (table `__flip_map__`, e.g. `^` and `v`, `A` and `V`, `_` becomes `-`). |
| `-s` | Strip empty leading and trailing lines; **also removes trailing whitespace of the last line** (`rstrip()`). |
| `-n` | Exactly one empty line before and after (after stripping). **If `-s` is also given, `-s` wins and `-n` is ignored.** |

Order in `main()`: render, then `-r`, then `-F`, then `-s` (else `-n`), then write the text as UTF-8 followed by one extra `\n`.

Out of scope (the task page says so): `-c` colour, `-L` font install, `-l` font list, `-i` font info.

## Smushing: how two neighbouring letters are squeezed together

Each font header has a "layout" number. Its bits switch the rules on (`SM_*` constants in `FigletBuilder`):

| Bit | Name | Meaning |
|---|---|---|
| 1 | equal | two identical characters become one |
| 2 | lowline | `_` is eaten by any of `\| / \ [ ] { } ( ) < >` |
| 4 | hierarchy | classes in order `\|`, `/ \`, `[ ]`, `{ }`, `( )`, `< >`; when two different classes meet, the one **later** in this list survives |
| 8 | pair | `[]`, `{}`, `()` (either order) become `\|` |
| 16 | big X | `/` + `\` -> `\|`, `\` + `/` -> `Y`, `>` + `<` -> `X` |
| 32 | hardblank | two hardblanks become one hardblank |
| 64 | kerning | letters are only pushed together until they touch (no merging) |
| 128 | smush | smushing is on; with bits 1-32 all off it is "universal" overlapping |

Results of the real `smushChars` (my test calls it directly, `left` then `right`):

| Rule | Example | Result |
|---|---|---|
| 1 equal | `\|` + `\|` | `\|` |
| 1 equal | `a` + `b` | no smush (None) |
| 2 lowline | `_` + `\|` | `\|` |
| 2 lowline | `/` + `_` | `/` |
| 2 lowline | `_` + `_` | none (only the equal rule could merge them) |
| 3 hierarchy | `\|` + `/` | `/` (same result in the other order, `/` + `\|`) |
| 3 hierarchy | `[` + `{` | `{` |
| 3 hierarchy | `(` + `<` | `<` |
| 3 hierarchy | `/` + `\` | none (same class) |
| 4 pair | `[` + `]` | `\|` |
| 4 pair | `)` + `(` | `\|` |
| 5 big X | `/` + `\` | `\|` |
| 5 big X | `\` + `/` | `Y` |
| 5 big X | `>` + `<` | `X` |
| 5 big X | `<` + `>` | none |
| 6 hardblank | `$` + `$` (hardblank) | `$` |
| 6 hardblank | `$` + `a` | none |
| kerning only (64) | `\|` + `\|` | none; a space next to a letter lets the letter move in |
| universal (128) | `a` + `b` | `b` (the later letter wins; right-to-left: the earlier one wins) |
| any rule | one of the two letters has width < 2 | never smushed |

Where the task page and the real code differ (my "rare cases" list):

1. The page says "`/` and `\` meet as an X". In the code `/`+`\` gives `\|`, `\`+`/` gives `Y`, and only `>`+`<` gives `X`.
2. `-n` loses against `-s` (see above). Easy to get wrong.
3. `-s` also rstrips the last row (trailing spaces disappear), `-n` does not strip that way.
4. `'' in 'abc'` is `True` in Python. In `smushChars` the left character can be the empty string, so the lowline/hierarchy tests can fire on `''`. A port must keep the same test (Go `strings.Contains(a, "")` is also true).
5. Characters the font does not have are silently dropped; a text made only of such characters prints just `\n`.
6. A newline inside the text ends the current line.
7. Width too small for a letter: Python raises `CharNotPrinted` and prints nothing to stdout (exit 1). Some width/letter pairs make the original loop forever (the generator uses a timeout and drops those cases).
8. `center` truncates toward zero (`int()` of a float), `right` uses `width - len - 1`. Negative counts mean no padding (`' ' * n` is empty for n < 0).
9. Right-to-left swaps left/right inside `smushRow` and `smushAmount`; `justify=auto` then means `right`.
10. `reverse()` and `flip()` use `str.splitlines()`, then rebuild with one `\n` per row.
11. Fonts are decoded as UTF-8 with `replace`; header token 0 is the hardblank; lines after the 95 ASCII glyphs and 7 German glyphs are only read if their first word starts with `0x`, so decimal code tags like `160 NO-BREAK SPACE` are skipped.

Font headers of the eight task fonts (`flf2a$ height baseline maxlen oldlayout commentlines printdir fulllayout codetags`):

| font | height | old layout | print dir | full layout |
|---|---|---|---|---|
| standard | 6 | 15 | 0 | 24463 |
| slant | 6 | 15 | 0 | 18319 |
| small | 5 | 15 | 0 | 22415 |
| big | 8 | 15 | 0 | 24463 |
| mini | 4 | 0 | 0 | 1920 |
| banner | 8 | 0 | 0 | 64 (kerning only) |
| shadow | 5 | 0 | 0 | 4992 |
| script | 7 | 0 | 0 | 3904 |

## Facts frozen while building the task

Frozen inputs (so a later change is noticed):

| What | sha256 |
|---|---|
| `pyfiglet/__init__.py` at the pinned commit | `09f3d07bc8d34905153c52c2e1e5316ae4f4dce5c6e88fa2bbfead1f6ac52c55` |
| `tests/data/visible.jsonl` (2000 cases) | `cd74ef5aaa25faf5aaf09c2fd3776d47ea3a8c997c0ff86fe00522aad451bce8` |
| `tests/data/hidden.jsonl` (2000 cases) | `15643130d468d9dd9d264adf43f2f4c304707d9b45b3cf1fa8ad6cc799b42864` |

The eight font hashes are in `tests/gen.py` (`FONT_SHA256`); `gen.py` refuses to run if any of them differs.

How the cases were made: `random.Random(7)`, 4136 candidate cases tried, 82 dropped because the original failed (76 times `CharNotPrinted`: width too small for a letter) or looped forever (6 times), 54 dropped because the output was blank (a program that prints nothing must never match a case), the rest split into 2000 visible + 2000 hidden with no argument list in both. Generating twice gives byte-identical files. A sample of 300 hidden cases was also re-run through the real `python -m pyfiglet` command line: 0 differences from the stored `out`.

Coverage of the hidden file: every font 210-248 cases (+170 with the default font), widths 10/20/40/60/80/120 (+323 default 80), `-D right-to-left` 509 cases of which 90 with width <= 20, `-r` 486, `-F` 469, `-s` 495, `-n` 521, 446 cases that wrap onto more than one figure, 250 with non-ASCII text, 57 with a newline inside the text.

Oracle evidence (Go port, written line by line from the Python):

- visible 2000/2000 and hidden 2000/2000 identical to the original;
- 20,000 extra random cases (seed 12345, all 72 fonts of `fonts-standard`, widths 1-60 plus the exam widths, random text from ASCII/Latin-1/missing glyphs/newlines) compared with the original run in-process: 0 differences (1,071 other cases skipped because the original itself fails or prints nothing);
- one bug found by reading before the first run: the header field for the old layout is `header[4]`, not `header[3]`.

Things I only learned by running (go on the "rare cases" list):

- `go build ./...` on a single `main` package writes an executable named after the module into the current folder. The oracle and the grader send it to a scratch folder with `-o dir/`.
- A verifier in the shared mode runs as the image's last `USER` unless `[verifier] user` says otherwise; this task sets `user = "root"` so the grader can keep `/tests` private and drop privileges for the program under test.
- The pinned original has no hard limit on loops: some width/letter pairs make `FigletBuilder` loop forever (it keeps cutting an empty buffer). `gen.py` uses a one-second alarm; the Go port stops after one million cuts.
