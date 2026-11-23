# NOTES — python-titlecase

- **Repo:** https://github.com/ppannuto/python-titlecase
- **Commit SHA:** `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- **Commit date:** 2024-04-05T22:03:59-07:00
- **Version:** 2.4.1 (`titlecase/__init__.py`, 293 lines)
- **Licence:** MIT (`LICENSE.txt`, © 2021 Patrick William Pannuto) — allowed (MIT / BSD / Apache).

## Important: which Python is "the truth"?

`titlecase/__init__.py` does `try: import regex` and silently falls back to the standard-library `re`.
The two code paths use different patterns (`\p{Letter}` vs `\w` / `[a-zA-Z]`) and **give different answers**:
with the `regex` package installed, 64 of the 4000 generated lines change
(e.g. `v1.2` → `V1.2`, `MC_X` → `Mc_X`, `_ab` → `_Ab`).
The task therefore pins the reference to **the `re` fallback** (`tests/gen.py` blocks `regex`) and says so in `instruction.md`.

## Rules applied by `titlecase()` (numbered, every example run against the original)

Input is split into lines, each line into words on single whitespace characters (`\s`); the original
whitespace is put back unchanged. For each word the **first rule that matches wins**, in this order:

1. **All-caps line.** If `line.upper() == line`, the line is "all caps". `THE LORD OF THE RINGS` → `The Lord of the Rings`.
   (In an all-caps line, words with internal capitals are *not* preserved; they are lower-cased and capitalised.)
2. **Initials in an all-caps line are kept.** `J.R.R. TOLKIEN` → `J.R.R. Tolkien`.
3. **Apostrophe after d / o / l.** `o'neil` → `O'Neil`; `d'artagnan` → `d'Artagnan`; `l'amour` → `l'Amour`; `d'accord` → `d'Accord`; `o'brien's` → `O'Brien's`.
   (`d` and `l` stay lower-case, `o` is capitalised; the letter after the apostrophe is upper-cased.)
4. **Mc / Mac prefix.** `mcdonald and MCDONALD` → `McDonald and McDonald`; the rest of the word is title-cased recursively. `mc-donald` → `Mc-Donald`; a bare `mc` → `Mc`.
5. **Mr / Mrs / Ms / Dr.** `mr smith and dr jones` → `Mr Smith and Dr Jones` (no dot added; `dr.` is *not* matched by this rule).
6. **Inline period, or capital inside a word (not all-caps lines).** Kept as typed: `node.js and e.g. www.example.com` (unchanged), `my iPhone and eBay` → `My iPhone and eBay`, `Ab aB _aB` unchanged.
7. **Small words** (`a an and as at but by en for if in of on or the to v v. via vs vs.`) are lower-cased: `and`, `of`, `the`…
8. **Slash.** A word containing `/` but not `//` is split on `/`, each piece title-cased on its own (and *without* the first/last-word rule): `and/or tcp/ip` → `And/or TCP/Ip`; `x/` → `X/`. A word with `//` (URLs) is left for later rules: `http://example.com/a/b` is unchanged (it also has an inline period).
9. **Hyphen.** Split on `-`, pieces title-cased separately: `well-known state-of-the-art` → `Well-Known State-of-the-Art`; `self- -ish` → `Self- -Ish`.
10. **All-caps lines are lower-cased** before the next rule.
11. **All-consonant words longer than 2 letters become upper-case** (a, e, i, o, u, y count as vowels): `nth of the psst st` → `NTH of the PSST St`.
12. **Normal word:** upper-case the first `\w` character, skipping leading punctuation: `(hello) "world"` → `(Hello) "World"`. Note `_` counts as `\w`: `_under` stays `_under`.
13. **First word of the line:** a small word is capitalised even after leading punctuation: `a tale of two cities` → `A Tale of Two Cities`; `vs. v. via` → `Vs. V. Via`.
14. **Last word of the line:** a small word (optionally followed by one punctuation mark) is capitalised: `what are you waiting for` → `What Are You Waiting For`; `who is it?` → `Who Is It?`.
    (Rules 13/14 are skipped inside the recursive calls of rules 8 and 9.)
15. **Sub-phrases.** After `: . ; ? ! - – ‒ — ―` followed by exactly one space, a *lower-case* small word is capitalised, with no word-boundary check: `star wars: a new hope` → `Star Wars: A New Hope`; `hello. an example; or two` → `Hello. An Example; Or Two`.
16. **Whitespace is preserved:** `a  b<TAB>c` → `A  B<TAB>C`; leading/trailing spaces stay; an empty line stays empty.
17. **Callbacks, `preserve_blank_lines`, `normalise_space_characters`** exist but are not used (defaults only).

## Rare cases worth testing (all in the generator's pools)

- the `regex`-vs-`re` difference above (`v1.2`, `_ab`, `MC_X`);
- `TCP/IP` → `TCP/Ip` (slash pieces are title-cased as normal words, not acronyms);
- the sub-phrase rule has **no word boundary**: it only matches lower-case text and can hit part of a longer word that rule 6 kept as typed;
- `mcd` (3 letters) is *not* a Mc-name (it becomes `MCD`, an all-consonant word); `mc-donald` is not matched by rule 4 either, but still ends up `Mc-Donald` via rule 9;
- `d'` / `o'` with nothing after the apostrophe are not rule 3;
- all-consonant check uses ASCII only and treats `y` as a vowel (`gym`, `sky`, `fly` are normal words);
- Unicode: `\w`, `.upper()`, `.lower()` and `str.capitalize()` are Unicode-aware, `[a-zA-Z]` is not;
  curly quotes and the dashes `– ‒ — ―` are part of the punctuation class.

## Why a plain regex copy does not work in Go

`regexp` in Go has no look-ahead, look-behind or back-references, and `\b` / `\w` / `\s` are ASCII-only there
while Python's are Unicode. The port replaces every pattern with hand-written rune code
(`smallFirst`, `smallLast`, `subphrase`, `ucInitials`, `aposSecond`, `ucElsewhere`, `macMc`, `capFirst`, …);
the trickiest are the ordered alternation `v\.?|via|vs\.?` combined with `\b`, `UC_INITIALS` (needs a small DP because of
`(A\.|A\.B)+`), and `UC_ELSEWHERE` (lazy prefix + `[a-zA-Z]+[A-Z]+?`).
