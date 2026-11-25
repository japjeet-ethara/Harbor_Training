# NOTES: python-titlecase

| Item | Value |
|---|---|
| URL | https://github.com/ppannuto/python-titlecase |
| Commit SHA | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` |
| Commit date | `2024-04-05T22:03:59-07:00` (`git log -1 --format='%H %cI'`) |
| Version | 2.4.1 (`titlecase/__init__.py: __version__`) |
| Licence | MIT (`LICENSE.txt`, `setup.cfg: license = MIT`) |
| Reference run | CPython 3.12.13 (Unicode 15.0.0) with `regex==2024.11.6`, so `REGEX_AVAILABLE = True` |

## What it is

python-titlecase is a Python port of John Gruber's `titlecase.pl`. The function
`titlecase(text)` turns text into title case following the New York Times style: small
words (`a`, `of`, `the`, ...) stay lower case except at the start and end, words that
already have inner capitals (`iPhone`) or inline periods (`example.com`) are left alone,
all-consonant words become acronyms (`html` -> `HTML`), and there are special cases for
`Mc`/`Mac`, `O'Neil`, hyphens and slashes. Everything is in `titlecase/__init__.py`
(293 lines); `titlecase/tests.py` holds the project's own tests.

## Two versions of the rules in one file

The module tries `import regex` (the third-party `regex` package, extra `titlecase[regex]`).
If that fails it falls back to `re` with **different patterns** (`\w` instead of
`\p{Letter}`, ASCII `[A-Z]` instead of `\p{Uppercase_Letter}`). The two give different
answers, for example `v2.0 release`:

| Path | Output |
|---|---|
| `regex` installed (reference) | `V2.0 Release` |
| plain `re` (fallback) | `v2.0 Release` |

The answer files use the `regex` path. `golang:1.23` ships Python 3.11 **without**
`regex`, so running the original inside the room gives the fallback behaviour.

## Rules, in the order `titlecase()` applies them (all verified by running the code)

The text is split into lines on `[\r\n]+`; each line is split on single whitespace
characters (`regex` `\s`, kept as separators); each word goes through the first rule that
matches. `all_caps` = `line.upper() == line`.

| # | Rule | Input | Output |
|---|---|---|---|
| 1 | All-caps line + initials kept (`UC_INITIALS`, only when the line is all caps) | `THE U.S.A. AND U.K.` | `The U.S.A. And U.K.` |
| 2 | Apostrophe second letter (`APOS_SECOND`, `[dol]['‘]letters`): `d`/`l` stay lower, `o` goes upper, letter after the apostrophe goes upper | `d'artagnan o'neil l'oreal` | `d'Artagnan O'Neil l'Oreal` |
| 3 | `Mc` / `MC` prefix (`MAC_MC`), the rest is title-cased recursively. `Mac` is **not** special | `mcdonald macdonald MCGREGOR` | `McDonald Macdonald McGregor` |
| 4 | `Mr`, `Mrs`, `Ms`, `Dr` (whole word): first letter upper | `mr smith and dr jones` | `Mr Smith and Dr Jones` |
| 5 | Inline period or inner capital kept as is (`INLINE_PERIOD`, `UC_ELSEWHERE`; the second only when the line is not all caps) | `the iPhone and eBay`, `visit example.com` | `The iPhone and eBay`, `Visit example.com` |
| 6 | Small words lower case (`SMALL_WORDS`: a an and as at but by en for if in of on or the to v v. via vs vs.) | `THE WIND IN THE WILLOWS` | `The Wind in the Willows` |
| 7 | Slash (`/` but not `//`): each part title-cased with first/last disabled | `either/or and/or` | `Either/or and/or` |
| 8 | Hyphen: each part title-cased with first/last disabled | `step-by-step out-of-the-box` | `Step-by-Step Out-of-the-Box` |
| 9 | All-caps line: word is lower-cased before the next rules | `A MAN, A PLAN, A CANAL` | `A Man, a Plan, a Canal` |
| 10 | All consonants and longer than 2 letters: upper case | `html css xml st nth` | `HTML CSS XML St NTH` |
| 11 | Otherwise: first letter after leading punctuation goes upper (`CAPFIRST`) | `"hello" (world) [x]` | `"Hello" (World) [X]` |
| 12 | Small word first in line capitalised (`SMALL_FIRST`) | `a tale of two cities` | `A Tale of Two Cities` |
| 13 | Small word last in line capitalised, one trailing punctuation allowed (`SMALL_LAST`) | `what is it for?` | `What Is It For?` |
| 14 | Small word after `: . ; ? ! - – ‒ — ―` and one ASCII space capitalised (`SUBPHRASE`, case-sensitive) | `star wars: a new hope` | `Star Wars: A New Hope` |

`PUNCT` (used by rules 11-13 and `UC_ELSEWHERE`) is
``!"#$%&'()*+,-./:;?@[\]_`{|}~‒–—―‘“``. The right quotes `’` and `”` are **not** in it.

## Rare cases (places where a naive Go port is wrong)

1. **No look-arounds.** The course page says the Python uses look-ahead and look-behind.
   This commit has none (`grep -E '\(\?[=!<]'` finds nothing). The real problem is
   Unicode: Go's `regexp` `\b`, `\w` and `\s` are ASCII-only, the `regex` package's are Unicode.
2. **Unicode whitespace splits words:** `the\u00a0lord\u2003of the rings` -> `The\u00a0Lord\u2003of the Rings`. Python `str.isspace()` also counts `\x1c`-`\x1f`; `regex` `\s` does not.
3. **Full case mapping:** `ßeas` -> `SSeas`, `ﬁsh` -> `FIsh`, `ŉ` -> `ʼN`. Go's `unicode.ToUpper` maps one rune to one rune.
4. **Rule 11 uses `upper()`, not title case:** `ǆungla` -> `Ǆungla`, not `ǅungla`. (`capitalize()` would title-case, `'ǆa'.capitalize()` -> `ǅa`, but rules 3 and 12-14 only ever capitalize ASCII small words or `Mc`, so that difference never shows. A mutation test confirmed it.)
5. **Greek final sigma:** lower-casing `ΟΔΟΣ ΣΟΦΟΣ` gives `Οδος Σοφος` (`ς` at the end of a word, `σ` inside).
6. **Case-insensitive matching follows Unicode folding:** `(?i)s` matches `ſ` (U+017F), `(?i)k` matches `K` (U+212A, Kelvin), `(?i)i` matches `İ` (U+0130). So `İn` is a small word: `war İn peace` -> `War i̇n Peace` (lower-casing `İ` gives two characters, `i` + U+0307).
7. **Leading whitespace switches off the first-word rule:** `  a man of the world` -> `  a Man of the World` (the first "word" is the empty string).
8. **A line with no letters counts as all caps** (`'123'.upper() == '123'`), which changes rules 1, 5 and 9.
9. **`’` (right single quote) is not punctuation here:** `’tis the season` -> `’tis the Season`, and `d’angelo` is not rule 2.
10. **`SUBPHRASE` is case-sensitive and needs an ASCII space:** `one: The two` stays, `one:\u00a0a` is not touched.
11. **`v.` and `vs.`:** `apple v. orange vs. pear` -> `Apple v. Orange vs. Pear`.
12. **Digits:** `2nd place in 3d` -> `2nd Place in 3d` (`CAPFIRST` needs a letter right after the punctuation).
13. **The two code paths differ** (`v2.0 release`), see above.
