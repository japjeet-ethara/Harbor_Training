# Step 1 notes: pinned pyfiglet source

These notes describe commit `255827efbc09d662875dad50fa0edc1e1263bf45` only.
Labels used below:

- **Source-confirmed:** read from this tree, or from one call that is named in the text.
- **Consequence:** follows from that source without a separate runtime check.
- **Not run:** not executed. Treat runtime output as a candidate until it is run.
- **User-reported runtime evidence:** manual checks executed by the user in PowerShell outside this agent session.

Smush character-pair examples are readings of `smushChars`. In the initial analysis, they were not executed. Subsequent user-reported runtime checks verified two specific examples (`_` + `/` under lowline, `|` + `[` under hierarchy) in both argument orders under controlled settings; other examples and full glyph interactions remain unverified.
In the initial analysis, the only pyfiglet call actually run for this note was `FigletFont.preloadFont('standard')` on this checkout, which raised `ModuleNotFoundError: No module named 'pyfiglet.fonts'`. At that time, no CLI render, font copy, or package install was performed. Font-header integers were read from the `.flf` files with a separate scanner; those fonts were not rendered. (Subsequent user-reported manual runtime checks verified basic CLI rendering for standard and slant fonts, newline options, and the two controlled smushing pairs.)

## 1. Source

- URL: https://github.com/pwaller/pyfiglet
- SHA: `255827efbc09d662875dad50fa0edc1e1263bf45`
- Commit date: `2026-08-02T22:51:18+01:00`

`git rev-parse HEAD` matched that SHA. `git log -1 --format=%cI` printed `2026-08-02T22:51:18+01:00` (committer timestamp). The author timestamp is the same instant written as `2026-08-03T03:21:18+05:30`. The subject is `Return False from isValidFont for a missing font (#161)`. Package version in this tree is `1.0.4` (`pyfiglet/version.py`, line 1).

## 2. Licence

The exact name in `LICENSE`, line 3, is:

`The MIT License (MIT)`

`setup.py` lines 28 and 32 also say `MIT` and `License :: OSI Approved :: MIT License`. The name above is the one printed in `LICENSE`.

## 3. Why a render cannot find fonts immediately after cloning

**Where the standard fonts are stored.** In this checkout they are files under `pyfiglet/fonts-standard/` (`standard.flf` and the other `*.flf` / `*.flc` files, plus an empty `pyfiglet/fonts-standard/__init__.py`). Contributed fonts are a separate tree, `pyfiglet/fonts-contrib/`. This checkout has no `pyfiglet/fonts/` directory.

**Where the code loads them.** `FigletFont.preloadFont` (`pyfiglet/__init__.py`, lines 146–157) builds `<font>.tlf` and then `<font>.flf`, in that order, and looks in this order:

1. `importlib.resources.files('pyfiglet.fonts').joinpath(fn)` — the importable package `pyfiglet.fonts`, which is the directory `pyfiglet/fonts/`.
2. Only if that call returns and `path.exists()` is false: `./<font>.<ext>` relative to the process current directory, then each entry in `FONT_DIRECTORIES`.

`FONT_DIRECTORIES` (lines 61–70): on `win32`, only `%APPDATA%\pyfiglet`. Otherwise `/usr/local/share/pyfiglet/`, `/usr/local/share/figlet`, and `/usr/share/figlet`.

The loader never names `fonts-standard` or `fonts-contrib`. `setup.py` lines 57–58 install the package `pyfiglet.fonts` and package data `*.flf`, `*.flc`, `*.tlf` from that package. `MANIFEST.in` includes `pyfiglet/fonts/*.flf`, `*.flc`, and `*.tlf`, not `fonts-standard`.

The first lookup is not inside a `try`. On this checkout, `FigletFont.preloadFont('standard')` raised `ModuleNotFoundError` before `FontNotFound` and before the `./` and `FONT_DIRECTORIES` fallbacks. `main` (lines 1016–1018) catches only `FontNotFound`.

**Makefile font setup.** The copy itself is in two targets. Both depend on `clean` first (`Makefile`, lines 12–19):

```make
minimal:    clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	python3 -m build

full:    clean
	cp pyfiglet/fonts-standard/* pyfiglet/fonts
	cp pyfiglet/fonts-contrib/* pyfiglet/fonts
	python3 -m build
```

`minimal` copies only `pyfiglet/fonts-standard/*` into `pyfiglet/fonts`. `full` then also copies `pyfiglet/fonts-contrib/*` into that same directory. Those `cp` lines are the font setup.

Other setup operations in the same file are different steps:

- `clean` (lines 7–10) deletes `build/` and `pyfiglet/fonts/`, then `mkdir pyfiglet/fonts/`. That recreates an empty directory. It does not copy font files.
- `python3 -m build` on `minimal` and `full` builds the distribution after the copy.
- `publish` (lines 21–23) runs `twine check` and `twine upload` on `dist/*`.

`setup.py` lines 8–13 are another path, not a Makefile target: if `pyfiglet/fonts` is not already a directory, it `shutil.copytree`s `pyfiglet/fonts-standard` onto `pyfiglet/fonts`. It does not copy `fonts-contrib`. Because the condition is “directory missing”, an empty `pyfiglet/fonts` left by `make clean` does not take this branch. A plain clone does not run `setup.py` or `make`, so neither copy happens before a render.

## 4. Horizontal smushing

Constants are on `FigletBuilder` (`pyfiglet/__init__.py`, lines 533–541), described in the source as lifted from figlet 2.2.2:

| Name in source | Bit | Comment in source |
| --- | --- | --- |
| `SM_EQUAL` | 1 | smush equal chars (not hardblanks) |
| `SM_LOWLINE` | 2 | smush `_` with any char in the hierarchy |
| `SM_HIERARCHY` | 4 | hierarchy: `\|`, `/\`, `[]`, `{}`, `()`, `<>` |
| `SM_PAIR` | 8 | `[` + `]` -> `\|`, `{` + `}` -> `\|`, `(` + `)` -> `\|` |
| `SM_BIGX` | 16 | comment says `/` + `\` -> `X`, `>` + `<` -> `X` |
| `SM_HARDBLANK` | 32 | hardblank + hardblank -> hardblank |
| `SM_KERN` | 64 | kerning; not one of the six rules |
| `SM_SMUSH` | 128 | master switch for overlapping |

`font.smushMode` is the font header’s `fullLayout` (`loadFont`, lines 306–321). If the header has no full-layout field:

- `oldLayout == 0` becomes 64 (kern bit only).
- `oldLayout < 0` becomes 0.
- otherwise `(oldLayout & 31) | 128` (low five bits, plus `SM_SMUSH`). Bit 32 is not taken from `oldLayout`.

`baseline` and `maxLength` are parsed (lines 295–297) and not stored. `printDirection` is header field index 6 when present, otherwise `None`.

The mode value is whatever the font file contains. `standard.flf` line 1 is `flf2a$ 6 5 16 15 46 0 24463 229`, so hardblank `$`, print direction `0`, full layout `24463`. `24463` has bits 0, 1, 2, 3, and 7 set among the named flags: `SM_EQUAL | SM_LOWLINE | SM_HIERARCHY | SM_PAIR | SM_SMUSH`. It does not set `SM_BIGX`, `SM_HARDBLANK`, or `SM_KERN`. Higher bits are not read; the code only tests the named masks and `& 63`.

### Gates that apply before the six rules

`smushChars` (lines 779–862), in order:

1. If either side is an ASCII space, return the other side. This happens with or without `SM_SMUSH`, and it happens before the width test.

```text
left=' ', right='X'  -> 'X'
left='X', right=' '  -> 'X'
```

2. If `prevCharWidth < 2` or `curCharWidth < 2`, return `None`. A glyph of width 0 or 1 does not overlap a non-space.
3. If `SM_SMUSH` (128) is clear, return `None`. None of the six rules run. That is the kerning-only exit.
4. If `(smushMode & 63) == 0`, universal overlapping handles the pair and the six rules are not consulted. Mask `63` is bits 0–5 only, so `SM_KERN` (64) can still be set.

`smushAmount` (lines 728–777) returns 0 immediately when both `SM_SMUSH` and `SM_KERN` are clear, so the overlap loop in `smushRow` (lines 662–666) does not run. ASCII space is the only character stripped when measuring borders (`rstrip(' ')` / `lstrip(' ')`, lines 747–759). A border pair that `smushChars` accepts adds one extra column of overlap (lines 770–772). The amount used is the minimum across font rows.

### The six rules, in the order the code applies them

Examples assume `SM_SMUSH` is set, both glyph widths are at least 2, the pair is not caught by the space gate, and only the named rule bits are set unless a line says otherwise. “No smush” means `smushChars` returns `None`.

**1. `SM_HARDBLANK`, bit 32** (lines 817–824). Checked first among the six. If both characters are the font’s hardblank, return the left one. The hardblank character is header field 0 (`$` on `standard.flf`; it is not always `$`). If the bit is set and only one side is the hardblank, the next `if` returns `None`. Equal hardblanks therefore never reach `SM_EQUAL`. If the bit is clear, two hardblanks also hit that “either side is hardblank” return and do not smush.

```text
# font.hardBlank == '$' and SM_HARDBLANK set
left='$', right='$'  -> '$'
left='$', right='A'  -> no smush
left='A', right='$'  -> no smush
```

**2. `SM_EQUAL`, bit 1** (lines 826–828). If the characters are equal, return the left one. The “not hardblanks” comment is enforced by the hardblank return above, not by a separate test inside this `if`.

```text
left='A', right='A'  -> 'A'
left='A', right='B'  -> no smush
```

**3. `SM_LOWLINE`, bit 2, then `SM_HIERARCHY`, bit 4** (lines 830–848). These share one list. Lowline is appended first, then hierarchy, and the first matching pair wins. For a pair of classes `(weaker, stronger)`, the character in the stronger class is kept:

```text
left in weaker and right in stronger  -> right
right in weaker and left in stronger  -> left
```

Lowline’s classes are `'_'` and `'|/\[]{}()<>'`. `_` loses to every character in that second string. Two underscores do not match lowline.

```text
left='_', right='|'  -> '|'
left='|', right='_'  -> '|'
left='_', right='<'  -> '<'
```

Hierarchy classes, from weaker to stronger (lines 836–842):

```text
'|'   loses to  '/\\[]{}()<>'
'/\\'  loses to  '[]{}()<>'     # weaker class: slash and backslash
'[]'  loses to  '{}()<>'
'{}'  loses to  '()<>'
'()'  loses to  '<>'
```

Same-class pairs (`'['` and `']'`, `'<'` and `'>'`) do not match hierarchy.

```text
left='|', right='/'  -> '/'
left='/', right='|'  -> '/'
left='[', right='('  -> '('
left='<', right='('  -> '<'
left='[', right=']'  -> no hierarchy match
```

**4. `SM_PAIR`, bit 8** (lines 850–853). After the class list. If `left+right` or `right+left` is `'[]'`, `'{}'`, or `'()'`, return `'|'`. Order does not matter. Angles are not pairs.

```text
left='[', right=']'  -> '|'
left='}', right='{'  -> '|'
left='(', right=')'  -> '|'
left='<', right='>'  -> no smush from this rule
```

With both hierarchy and pair enabled, `'['` and `']'` still reach this rule because they are the same hierarchy class.

**5. `SM_BIGX`, bit 16** (lines 855–862). Last rule. The comment on line 538 says `/ + \ -> X` and `> + < -> X`. The body does something else:

```text
left='/', right='\\'  -> '|'
left='\\', right='/'  -> 'Y'
left='>', right='<'   -> 'X'
left='<', right='>'   -> no smush
```

Slash order changes the result (`'|'` versus `'Y'`). Angle brackets smush only when the left argument is `'>'` and the right argument is `'<'`.

No font under `pyfiglet/fonts-standard/` has bit 16 or bit 32 set in the effective layout (header full layout, or the old-layout conversion when full layout is absent). Those two rules are still implemented. In `pyfiglet/fonts-contrib/`, some headers do set them; for example `3d-ascii.flf` sets both `SM_BIGX` and `SM_HARDBLANK` together with the other controlled bits and `SM_SMUSH`. `make minimal` does not copy that tree.

### Kerning, separately

Kerning is `SM_KERN` (64), not a seventh overlap rule.

- `smushAmount` is allowed to be non-zero when either `SM_KERN` or `SM_SMUSH` is set (line 737).
- If `SM_SMUSH` is clear, `smushChars` returns `None` for every non-space pair (lines 797–799). Borders can move together until they touch, and the extra overlap column is not added. Spaces still collapse, because the space gate is earlier.
- If both bits are clear, `smushAmount` returns 0. Each glyph keeps its full stored width. No sliding.

`banner.flf` has full layout 64 (`SM_KERN` only). `block.flf`, `lean.flf` (576), `script.flf`, and `smscript.flf` (3904) also have the kern bit and not `SM_SMUSH`. `standard.flf` has `SM_SMUSH` and not `SM_KERN`, so its fitting is the controlled rules, not kern-only mode.

Consequence of the empty-buffer math in `smushAmount`, not rendered: for the first character in left-to-right mode the “previous” row is `''`, and the minimum number of leading ASCII spaces shared by every row becomes `maxSmush`. `addCurCharRowToBufferRow` then keeps `glyph[maxSmush:]` (line 671). When kern or smush is enabled, a first glyph whose every row has a leading space loses those columns. With both bits clear, `maxSmush` is 0 and those spaces stay.

### Universal smushing

Universal overlapping is the branch at lines 801–815: `SM_SMUSH` is on and `(smushMode & 63) == 0`. It is not one of the six rules, and it replaces them.

- Hardblank on the left returns the right character.
- Hardblank on the right returns the left character.
- Otherwise the later input character wins: return `right` in left-to-right mode, return `left` in right-to-left mode (lines 809–815). The comment there says the dominant character is the later character in the user’s text, not necessarily the rightmost cell.

```text
# left-to-right, universal, hardblank is '$'
left='A', right='B'  -> 'B'
left='$', right='B'  -> 'B'
left='A', right='$'  -> 'A'

# right-to-left, same mode; arguments are the values smushChars receives
left='A', right='B'  -> 'A'
```

In `fonts-standard`, full layouts with `SM_SMUSH` and none of bits 0–5 are `mini.flf` (1920), `smshadow.flf` (1920), and `shadow.flf` (4992).

### Direction-dependent behavior in the builder

`direction` does not walk the string backwards. `goToNextChar` always increments (`pyfiglet/__init__.py`, lines 579–580). Right-to-left changes how the current glyph is joined to the buffer:

- `smushAmount` swaps the current glyph and the buffer before measuring borders (lines 744–745).
- `smushRow` swaps them before overlap, so the new glyph is `addLeft` and the existing line is `addRight` (lines 659–660). The stored row becomes `addLeft + addRight[maxSmush:]` (line 671). Each new character is therefore prepended. The first character ends up on the right as a consequence of prepending in index order. This was not rendered.
- After that swap, `smushChars` sees the new glyph as `left` and the older glyph as `right`. `SM_EQUAL` and `SM_PAIR` are order-insensitive. `SM_LOWLINE` and `SM_HIERARCHY` keep the same winning character when the left and right arguments are swapped. `SM_BIGX` is order-sensitive: slash followed by backslash produces |, backslash followed by slash produces Y, and > followed by < produces X. Universal smushing uses direction to select the later input character.
- Auto justification follows the resolved direction (see section 5). That is separate from the prepend.

`Figlet.direction` (lines 886–897): `'auto'` uses the font’s `printDirection`. `0` and every value other than `1` become `'left-to-right'`. Only `1` becomes `'right-to-left'`. A missing print-direction field stays `None` and therefore becomes left-to-right. In `fonts-standard`, `ivrit.flf` is the file whose print direction is `1` (full layout `16271`, same controlled bits as `standard` plus no kern bit). `term.flf` uses hardblank `0x7F` and full layout `0`.

`-r` is a later mirror of the finished string. It is not this direction flag.

## 5. CLI flags

Defined in `main` (`pyfiglet/__init__.py`, lines 945–1044). The entry point is `pyfiglet = pyfiglet:main` (`setup.py`, lines 59–62). `pyfiglet/__main__.py` calls the same `main`. There is no stdin read. With no text arguments, `parser.print_help()` runs and `main` returns 1 (lines 1002–1004). Otherwise the arguments are joined with a single space (line 1009) and that string is rendered. `--` is whatever `optparse` does with this parser; this file does not customize it.

On Python 3, `main` detaches `sys.stdout` to binary (lines 1030–1032), writes the rendered UTF-8 bytes, then always writes one more `b'\n'` (lines 1038–1039). `FontNotFound` prints `pyfiglet error: requested font {name!r} not found.` and returns 1. `CharNotPrinted`, `FontError`, and `InvalidColor` are not caught here.

### `-f` / `--font`

Default `standard` (`DEFAULT_FONT`, line 52; option lines 948–950). Passed through as `Figlet(font=...)`. Lookup is the `preloadFont` order in section 3: `.tlf` before `.flf`, package `pyfiglet.fonts` first. A missing `pyfiglet.fonts` package raises `ModuleNotFoundError` from that lookup. A resolved package whose file is absent falls through to `./` and `FONT_DIRECTORIES`, and then raises `FontNotFound`.

Characters whose code is not in the loaded font are skipped (`getCharAt`, lines 611–619, and the `None` return at lines 554–555). The newline character is special and is not skipped that way (lines 549–552).

### `-w` / `--width`

Default `80`, type `int` (lines 960–962). Same default on `Figlet.__init__` (lines 870–875). This integer is both the wrap limit and the justification width.

For each input character that exists in the font, the builder sets

```text
currentTotalWidth = len(buffer[0]) + curCharWidth - maxSmush
```

(line 561). Only row 0’s current length is used, not the longest row. If `width < curCharWidth`, it raises `CharNotPrinted("Width is not enough to print this character")` (lines 556–557). If `currentTotalWidth >= width`, it wraps with `handleNewLine` instead of adding the character (lines 570–571). Equality wraps. The character that would reach the width starts the next line, or is retried there when the break is not a space (see candidates). Wrapping prefers the last recorded space: the saved buffer is the line from before that space was added, and the following `goToNextChar` advances past the space, so the space is the break and is not painted on the next line (`handleNewLine`, lines 703–708; blank saved at lines 563–564).

### `-D` / `--direction`

Choices `auto`, `left-to-right`, `right-to-left`. Default `auto` (lines 951–955). Resolution is `Figlet.direction` in section 4. `'auto'` does not inspect the terminal. It uses the font header: `standard.flf` has print direction 0, so auto is left-to-right.

The flag changes overlap orientation and prepend-versus-append. It does not reverse a finished line. `-r` does that later.

### `-j` / `--justify`

Choices `auto`, `left`, `center`, `right`. Default `auto` (lines 956–959). The help text says justification defaults to the print direction. The code maps direction to an alignment (`Figlet.justify`, lines 900–908):

- auto and left-to-right -> `'left'`
- auto and right-to-left -> `'right'`
- any explicit choice -> that choice, and direction does not override it

`'center'` is never the auto result. If auto were combined with a direction string other than those two, the property would fall off the end and return `None`. The CLI choices cannot produce that, because auto direction only returns the two names above.

`justifyString` (lines 710–721) runs once per wrapped line, after the glyphs are built and before hardblanks become spaces (`formatProduct`, lines 600–609):

- `'right'`: prepend `width - len(row) - 1` spaces. When the row is shorter than `width`, the arithmetic result length is `width - 1`. A multiplier that is not positive adds no spaces (Python repetition of a negative or zero count).
- `'center'`: prepend `int((width - len(row)) / 2)` spaces. The remainder stays on the right.
- `'left'`, and any other value including the auto-derived `'left'`: the method has no branch for it, so the row stays as built.

Padding is relative to the selected `-w` width, per row, using that row’s own length. Rows of different lengths get different amounts of padding. Hardblank characters still count toward `len(row)` because replacement happens after justification (lines 723–726). Left alignment does not pad out to the width; the wrap rule already stopped the line at `width`.

Direction and justification interact only through the auto mapping, plus the fact that right-to-left has already prepended glyphs before padding runs. `-D right-to-left -j left` still prepends glyphs and then does not pad. `-D left-to-right -j right` appends glyphs and then applies the right-pad formula. `-j` does not change `direction`.

### `-r` / `--reverse`

Default off (lines 963–964). After `renderText`, `FigletString.reverse` (lines 433–438) runs before flip and before `-s`/`-n` (lines 1020–1028). Each `splitlines()` row is translated and then reversed. `splitlines()` drops the terminator, and `newFromList` joins with `\n` and adds one trailing `\n` (lines 464–465).

The translation is not a full mirror of every glyph. Non-identity byte mappings in `__reverse_map__` (lines 396–404), extracted from that literal:

```text
( -> )    ) -> (    / -> \    \ -> /
< -> >    > -> <    [ -> ]    ] -> [
{ -> }    } -> {
```

Justification has already inserted spaces. Reversing a row moves those spaces to the other end. `-r` does not re-run `justifyString`.

### `-F` / `--flip`

Default off (lines 969–970). Applied after `-r` when both are set (lines 1021–1024). `flip` (lines 440–445) reverses row order, then translates each row. It does not reverse a row horizontally. Non-identity mappings in `__flip_map__` (lines 415–423):

```text
/ -> \    \ -> /    ^ -> v    v -> ^
A -> V    V -> A    M -> W    W -> M
P -> b    R -> b    b -> P
m -> w    w -> m    _ -> -
```

`P` and `R` both become `b`, and `_` becomes `-` while `-` stays `-`. The map is lossy. Brackets, braces, and parentheses are unchanged by the flip map (they are changed by the reverse map).

### `-s` / `--strip-surrounding-newlines` and `-n` / `--normalize-surrounding-newlines`

Both default off (lines 965–968). The branch is `if -s` / `elif -n` (lines 1025–1028). When both are passed, `-s` runs and `-n` does not.

`strip_surrounding_newlines` (lines 449–459):

- Walks `splitlines()` rows.
- Drops leading rows whose `row.strip()` is empty.
- After the first row that contains a non-whitespace character, keeps later rows, including empty ones.
- Rebuilds the string and calls `rstrip()` with no arguments. That removes trailing newlines and also other trailing whitespace, including spaces on the last kept line. The comment says it is there to remove trailing newlines; the call is a full `rstrip()`.

`normalize_surrounding_newlines` (lines 461–462) is `'\n' + strip_surrounding_newlines() + '\n'`. It therefore inherits the leading-row removal and the full trailing `rstrip()`, then adds one newline on each side.

`main` then appends another `b'\n'`. Consequence, composing those operations, not re-rendered here:

- Default: each finished line group already ends in `\n` (`replaceHardblanks`, line 724), and `main` adds one more `\n`.
- `-s`: the renderer’s trailing newline and trailing spaces are stripped, then `main` writes one `\n`. Leading blank rows are gone.
- `-n`: a leading `\n`, the stripped body, the normalize `\n`, and `main`’s `\n`.

`pyfiglet/tests/test_cli.py` encodes expected CLI text for `pyfiglet -f slant -s 0` (lines 15–26) and `pyfiglet -f slant -n 0` (lines 67–80). The `-s` expectation starts on the first art row and has a single trailing newline. The `-n` expectation has a blank line before the art and a blank line after it. Those tests were not run for this note. The comment on line 67 says normalize is strip with padding, which matches `normalize_surrounding_newlines` calling `strip_surrounding_newlines`.

## 6. Candidate cases for later testing

All of the following are candidates derived from the source during initial analysis. Except for the specific CLI renders (standard-font `Hello` and slant-font `hello`) and the two controlled `smushChars` pairs later verified by the user, none of them were confirmed by rendering; other examples and full glyph interactions remain unverified.

**Layout modes already present in the font files**

- Controlled rules on the default font: `standard.flf` full layout `24463` (`EQUAL`, `LOWLINE`, `HIERARCHY`, `PAIR`, `SM_SMUSH`), print direction 0, hardblank `$`. `big.flf` uses the same `24463`. `slant.flf` (`18319`), `small.flf` and `smslant.flf` (`22415`), `bubble.flf` (`10127`), and `ivrit.flf` (`16271`) set those same five flags. `digital.flf` is only `EQUAL | SM_SMUSH` (`16513`).
- Universal: `mini.flf`, `smshadow.flf` (both `1920`), `shadow.flf` (`4992`).
- Kern only: `banner.flf` (`64`), `block.flf` and `lean.flf` (`576`), `script.flf` and `smscript.flf` (`3904`).
- No kern and no smush: full layout 0, or `oldLayout < 0` with no full-layout field, which `loadFont` converts to 0. `term.flf`, `mnemonic.flf`, and `blocky_25.flf` store 0. Most other `fonts-standard` files have a short header whose old layout is `-1` (`times.flf`, `cour.flf`, `helv.flf`, and the other short headers found by the scanner).
- Right-to-left font header: `fonts-standard/ivrit.flf` print direction 1. `fonts-contrib/mshebrew210.flf` is `flf2a$ 4 3 10 -1 13 1` (print direction 1, no full layout, old layout `-1`, so effective mode 0). Contrib also has `jerusalem.flf` and `mirror.flf` with print direction 1.
- `SM_BIGX` and `SM_HARDBLANK` need a font outside `fonts-standard`, or a fixture. Contrib examples exist (`3d-ascii.flf` sets both bits). `make minimal` will not put them on the load path.
- Hardblank is not always `$`. `term.flf`, `bubble.flf`, and `digital.flf` use `0x7F`. Replacement with a normal space happens only at the end (`replaceHardblanks`), so a hardblank still occupies a column during smush and justify.
- `fonts-standard/*.flc` (`upper.flc` starts with `flc2a`) are copied and listed in package data, but `preloadFont` only opens `.tlf` and `.flf`. The magic test is `^[tf]lf2.` (line 126), which does not match `flc2a`.
- `pyfiglet/fonts-contrib/ascii9.tlf` begins with ZIP bytes `PK\x03\x04`. `preloadFont` and `isValidFont` treat a zip as a font and read the first member (lines 159–165 and 196–200). The inner member was not inspected.

**Builder and parser edges**

- `width == glyph width` on a non-space, with `maxSmush == 0`: `width < curCharWidth` is false, then `currentTotalWidth >= width` is true. With no saved space, `cutBufferAtLastChar` decrements the iterator (lines 688–691) and the render loop increments it again (lines 487–489). The same character is retried on an empty buffer. That control flow does not advance through the text. `CharNotPrinted` is only for `width < glyph width`, and `main` does not catch it.
- A space that itself crosses the width is recorded as a blank and then skipped by `goToNextChar`. That path does advance.
- Unknown characters and empty non-space glyphs are omitted. Space is stored even when its glyph is empty (lines 348–356). A string of only unknown characters never fills `buffer[0]`, so `returnProduct` does not flush it (lines 586–587) and the CLI still writes `main`’s extra newline.
- An input newline flushes immediately (lines 549–552). The later newline test at lines 566–568 is unreachable because of that return.
- `handleNewLine` with no recorded space appends the current buffer and retries the current character. The wrap decision used `len(buffer[0])` only, so another row can be longer than the width.
- `updateSmushedCharInLeftBuffer` assigns `smushChars`’s return value even when it is `None` (lines 647–652 and 665–666). `''.join` of a list containing `None` would raise. Whether any real overlap produces `None` was not executed. The `idx == len(addLeft)` check uses `idx > len(l)` rather than `>=` (line 649); the `i` loop as written reaches at most `len(addLeft) - 1`.
- Extended glyphs are loaded only when the code token matches `(?i)^0x` (lines 367–378). A decimal code is not converted and does not consume the following glyph lines, so the parser can desynchronize. After ASCII 32–126, the next seven glyphs are always read as `ÄÖÜäöüß` if any data remains (lines 358–364), before the `0x` section.
- Glyph end markers: the last non-space character of the first row is the end mark, and one or two trailing copies are stripped (lines 337–341).
- Code points `U+0085`, `U+2028`, and `U+2029` are replaced with a space before `splitlines` (lines 278–280).
- `oldLayout == 0` with no full-layout field becomes kern-only (64). `oldLayout > 0` with no full-layout field becomes `(oldLayout & 31) | 128`, which cannot set `SM_HARDBLANK`. The short headers in `fonts-standard` that were scanned use `-1`, so they take the mode-0 conversion instead. The positive conversion is still in `loadFont`.
- First-glyph leading spaces (left-to-right) or trailing spaces (right-to-left) can be trimmed when `SM_KERN` or `SM_SMUSH` is set, as described in section 4.
- Right justification’s pad is `width - len(row) - 1`. Center padding is the floor of half the gap. Empty rows produced by a newline are passed through `justifyString` as well.
- `-s` / `-n` can delete trailing spaces on the last line because strip uses `rstrip()`. A right-justified or center-padded last line is exposed to that. Leading rows that contain only spaces are also dropped (`row.strip() == ''`).
- `-r` after `-j right` mirrors the padding spaces to the opposite side. `-F` after `-r` flips that already mirrored text and then applies the lossy flip map (`R` and `P` both become `b`, `_` becomes `-`).
- `-s` together with `-n` keeps only `-s`.
- `-D right-to-left` with `-j left`, and `-D left-to-right` with `-j right` or `-j center`, separate building direction from padding.
- `-w` equal to a glyph width, `-w` smaller than a glyph width, and a negative `-w` (the option type is `int`, so the choice list does not reject it) exercise the `>=` wrap, `CharNotPrinted`, and the space-pad multiplier.
- `pyfiglet` with no arguments returns 1 after help. `pyfiglet ''` still has one argument; the joined text is empty. That path was not run.
- `-f` of a missing font when `pyfiglet/fonts` exists but does not contain the file should reach `FontNotFound`. When the package directory itself is absent, the observed failure is `ModuleNotFoundError` instead, and it is not the message at lines 1016–1018.
- `make clean` creates an empty `pyfiglet/fonts/` and does not copy `__init__.py`. Whether `importlib.resources.files('pyfiglet.fonts')` succeeds against that empty directory was not run. `setup.py` will not `copytree` into a directory that is already present.
- A `.tlf` and `.flf` with the same stem: `.tlf` is chosen first (lines 146–151).
- Zip install via `-L` (`installFonts`, lines 242–271) and a zipped font opened by `-f` are separate from the Makefile `cp`.

## User-verified runtime checks

The following checks were run manually by the user in PowerShell and are recorded here as user-reported runtime evidence, not commands executed by the agent:

### Environment
- Windows, Python 3.13.17.
- Interpreter:
  `C:\Users\Abhishek\AppData\Local\Programs\Python\Python313\python.exe`
- UTF-8 mode enabled; bytecode generation disabled.
- Imported pyfiglet from this local checkout.
- Standard fonts copied from pyfiglet/fonts-standard to pyfiglet/fonts.
- FigletFont.preloadFont('standard') succeeded.

### CLI verification
- `python -m pyfiglet -f standard Hello`
- Exit code 0, empty stderr, nonempty art.
- Output contains no carriage-return bytes and ends with LF LF.
- The pinned CLI rendered lowercase "hello" with -f slant successfully, with exit code 0 and empty stderr.

### Newline checks for the same standard-font Hello input
- Default: 139 bytes.
- -s: 114 bytes.
- -n: 116 bytes.
- -s -n: 114 bytes, exactly equal to -s.
- Verified:
  stripped == default.rstrip() + b"\n"
  normalized == b"\n" + default.rstrip() + b"\n\n"
- All assertions passed; verification script exit code 0.

### Direct smushChars checks
- Direct smushChars checks used an initialized FigletBuilder and a controlled font fixture: height 1, hardblank "$", glyph widths 2, SM_SMUSH plus only the rule being tested.
- Lowline: "_" + "/" produced "/" in both argument orders.
- Hierarchy: "|" + "[" produced "[" in both argument orders.
- Both assertions passed; verification script exit code was 0.
- Status: these two examples are now verified under controlled settings. Other examples and full glyph interactions remain unverified.

### Verification lesson
An earlier check failed because it accessed SM_LOWLINE on the class and bypassed initialization. The constants are instance attributes set by FigletBuilder.__init__. Correcting the check resolved the failure. This was a verification-script mistake, not a pyfiglet defect.

*Note on scope:* These runtime checks verify standard-font `Hello` rendering and its newline options, slant-font lowercase "hello", and two controlled character-pair smushing checks. They do not claim or prove that all inputs work. Other examples and full glyph interactions remain unverified.

## What was not confirmed

- In the initial analysis, no figlet string was rendered, and none of the character-pair examples were executed. Subsequent user-reported checks confirmed standard-font `Hello` and slant-font `hello` CLI renders, as well as two character-pair examples (`_` + `/` for lowline, `|` + `[` for hierarchy in both argument orders) under controlled settings. These two examples are now verified under controlled settings. Other examples and full glyph interactions remain unverified.
- `pyfiglet/tests/test_cli.py` was read, not run.
- The inner contents of zipped `.tlf` files were not unpacked.
- Fallback behavior once `pyfiglet/fonts` exists as an empty directory was not run.
- Optparse’s exit status for an illegal `-D` or `-j` choice is not set in this file; it was not run.
- Author and committer timestamps are one instant in two offsets. The commit date requested by the assignment matches the committer timestamp.
