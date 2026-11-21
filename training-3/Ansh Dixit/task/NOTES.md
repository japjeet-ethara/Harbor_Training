# NOTES: python-titlecase

- Repo: https://github.com/ppannuto/python-titlecase
- Commit SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: 2024-04-05T22:03:59-07:00
- Version: 2.4.1
- Licence: **MIT** (allowed: MIT / BSD / Apache)
- Code path used as ground truth: stdlib `re` (the optional `regex` package is blocked in `tests/gen.py` and not installed in the image).

## Rules of `titlecase()` (verified against the original)

### 1. Whole-line handling
Each line is processed on its own. The line is split on single whitespace characters and the original spaces/tabs are kept when it is joined again.

| input | output |
|---|---|
| `the  lord\tof the rings` | `The  Lord\tof the Rings` |

### 2. All-caps lines
If the whole line is upper case, every word is lower-cased first and is not treated as an acronym.

| input | output |
|---|---|
| `THE LORD OF THE RINGS` | `The Lord of the Rings` |
| `NASA LAUNCHES ROCKET` | `Nasa Launches Rocket` |

### 3. Small words stay lower case
`a an and as at but by en for if in of on or the to v v. via vs vs.` are lower-cased, **unless** rule 12 applies first (a word like `VS` in a mixed-case line keeps its capitals).

| input | output |
|---|---|
| `war and peace` | `War and Peace` |
| `cats VS dogs` | `Cats VS Dogs` |
| `a tale of two cities` | `A Tale of Two Cities` |

### 4. First and last word are always capitalised
Even if they are small words, with leading punctuation skipped.

| input | output |
|---|---|
| `the end of the` | `The End of The` |
| `what are you waiting for` | `What Are You Waiting For` |
| `"a" is for apple` | `"A" Is for Apple` |

### 5. Sub-phrase rule
After `: . ; ? ! -` (and dash variants) plus one space, a small word is capitalised. The match has no word boundary and is case-sensitive.

| input | output |
|---|---|
| `foo: the bar` | `Foo: The Bar` |
| `wait! and then what? of course` | `Wait! And Then What? Of Course` |
| `x: inPut` | `X: InPut` |

### 6. Hyphenated words
Each part is titlecased separately, with small-word handling for first/last off. The last-word rule is applied afterwards on the whole token.

| input | output |
|---|---|
| `self-aware robots` | `Self-Aware Robots` |
| `state-of-the-art` | `State-of-the-Art` |
| `a long foo-of` | `A Long Foo-Of` |

### 7. Slashed words
Each part is titlecased separately (not if the word contains `//`).

| input | output |
|---|---|
| `and/or` | `And/Or` |
| `read/write access` | `Read/Write Access` |
| `http://x.com/a` | `http://x.com/A` |

### 8. Mc / Mac names
`Mc`, `mc` or `MC` followed by 2+ more characters: prefix becomes `Mc`, the rest is titlecased recursively.

| input | output |
|---|---|
| `mcdonald's farm` | `McDonald's Farm` |
| `MCDONALD` | `McDonald` |
| `mcq` | `MCQ` |

### 9. Mr / Mrs / Ms / Dr
Only the first letter is upper-cased; the rest is left as typed.

| input | output |
|---|---|
| `dr jekyll and mr hyde` | `Dr Jekyll and Mr Hyde` |
| `MR smith` | `MR Smith` |
| `ms. jones` | `Ms. Jones` |

### 10. Apostrophe second letter
`d'`, `o'`, `l'` + letters: first letter lower-cased (consonants) or upper-cased (`o`), third letter upper-cased.

| input | output |
|---|---|
| `o'neil` | `O'Neil` |
| `d'artagnan` | `d'Artagnan` |
| `l'amour` | `l'Amour` |

### 11. Inline period
A letter-period-letter inside a word (domains, file names) leaves the word untouched.

| input | output |
|---|---|
| `visit example.com now` | `Visit example.com Now` |
| `file.txt` | `file.txt` |
| `v1.2 released` | `v1.2 Released` |

### 12. Internal capitals kept
In a mixed-case line, a word with a capital after its first letter is left alone.

| input | output |
|---|---|
| `the iphone and ebay` | `The Iphone and Ebay` |
| `buy iPhone cases` | `Buy iPhone Cases` |
| `NASA and the moon` | `NASA and the Moon` |

### 13. Short all-consonant words become acronyms
More than 2 letters, no vowels (y counts as a vowel). Note `tv` has only 2 letters and `nyc` contains `y`, so neither becomes an acronym; `hmm`, `tsk`, `brr` do.

| input | output |
|---|---|
| `tv shows` | `Tv Shows` |
| `the nyc subway` | `The Nyc Subway` |
| `hmm tsk brr` | `HMM TSK BRR` |

### 14. Initials in all-caps lines
Words like `J.R.R.` are kept as typed when the line is all caps.

| input | output |
|---|---|
| `J.R.R. TOLKIEN` | `J.R.R. Tolkien` |
| `U.S.A. TODAY` | `U.S.A. Today` |

### 15. Capitalise first word character
Leading punctuation is skipped. Digits and underscores count as word characters, so they stop the search and the next letter is NOT capitalised.

| input | output |
|---|---|
| `"hello" (world)` | `"Hello" (World)` |
| `1st place` | `1st Place` |
| `_foo bar` | `_foo Bar` |
| `__init__ file` | `__init__ File` |

### 16. Quirks worth testing
Rare paths that careless ports get wrong.

| input | output |
|---|---|
| `a--b` | `A--B` |
| `-leading trailing-` | `-Leading Trailing-` |
| `w/o a//b` | `W/O A//b` |
| `of. to! vs.` | `Of. To! Vs.` |
| `cats vs. dogs v. cats` | `Cats vs. Dogs v. Cats` |

## Step 1 spot checks (done by running the original)

Every example above was produced by running `titlecase()` from this exact commit, not typed by hand. Three checked in a terminal:

    python3 -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"   ->  The Lord of the Rings
    python3 -c "from titlecase import titlecase; print(titlecase('MCDONALD'))"                ->  McDonald
    python3 -c "from titlecase import titlecase; print(titlecase('_foo bar'))"                ->  _foo Bar

## What makes the task hard (measured)

The Go port in `solution/solve.sh` scores 1.0. These are single, natural mistakes, each applied to that port and scored on the hidden set (`behaviour` = share of 2000 hidden lines that match; `total` = full reward):

| mistake | behaviour | total |
|---|---|---|
| '_' treated as a non-word character | 0.857 | 0.905 |
| last-word rule skipped (SMALL_LAST) | 0.952 | 0.968 |
| sub-phrase rule made case-insensitive | 0.997 | 0.998 |
| internal-capitals rule (UC_ELSEWHERE) off | 0.835 | 0.890 |
| apostrophe rule (d'/o'/l') off | 0.885 | 0.924 |
| Mc/Mac rule off | 0.905 | 0.937 |
| all-consonant acronym rule off | 0.861 | 0.907 |
| hyphen parts get first/last rule (recursion flag true) | 0.875 | 0.916 |
| initials-in-all-caps rule off | 0.997 | 0.998 |

The rules that ports most easily get wrong are the ones that depend on Python regex details: `\w` includes the underscore (so `_foo` is not capitalised), `SUBPHRASE` has no word boundary and is case-sensitive, `UC_ELSEWHERE` is case-sensitive and skips leading punctuation, the last-word rule is applied again to a hyphenated token, and `APOS_SECOND` needs backtracking for its optional `'s` tail.

## What I would add to make it harder

- Non-ASCII letters (Python `\w`, `upper()` and `lower()` follow Unicode: `ß` becomes `SS`).
- The `regex` package code path (`\p{Letter}` instead of `\w`) as a second hidden set.
- Callback / word-list support and `preserve_blank_lines`, `normalise_space_characters` flags.
