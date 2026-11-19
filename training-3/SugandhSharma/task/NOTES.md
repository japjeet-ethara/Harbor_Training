# NOTES: the source of this task

Author of the task: sugandhsharma.

## 1. Source

- Repository: https://github.com/ppannuto/python-titlecase
- SHA: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00`
- Package version: 2.4.1 (`__version__` in `titlecase/__init__.py`)
- Code read: `titlecase/__init__.py` (293 lines). The project's own tests are in `titlecase/tests.py`.
- `environment/python-titlecase/` is an unchanged copy of that commit, without its `.git` and `.github` folders.

## 2. Licence

MIT. File `LICENSE.txt`: "The MIT License (MIT)", "Copyright (c) 2021 Patrick William Pannuto".
MIT is one of the licences allowed for this exercise (MIT, BSD, Apache).

## 3. Reference mode

The original has two code paths. If the optional `regex` package is installed it uses Unicode letter classes;
if not, it uses the standard library `re`. `regex` is an optional extra and is not installed by a plain
`pip install titlecase`. The two paths give different answers:

| Input | Without `regex` (the reference) | With `regex` |
|---|---|---|
| `version v2.0 is out` | `Version v2.0 Is Out` | `Version V2.0 Is Out` |
| `__init__ method` | `__init__ Method` | `__Init__ Method` |

The reference for this task is `titlecase(line)` with default arguments on the standard-library path
(`REGEX_AVAILABLE` is `False`). `tests/gen.py` switches `regex` off before it imports the original, so the
answers are the same on every machine. The answers in `tests/data` were frozen with Python 3.13.1.

Input characters: printable ASCII, tab, the curly quotes U+2018, U+2019, U+201C, U+201D and the dashes U+2012,
U+2013, U+2014, U+2015. Outside this set Python and Go disagree about letters and upper case, so the set is
stated in `instruction.md` and `tests/gen.py` checks every title against it.

## 4. Rules

In the order the code applies them. Every example was produced by running the original in the reference mode.

| # | Rule | Where in the code | Example |
|---|---|---|---|
| 1 | The text is split into lines; each line is handled alone | `regex.split('[\r\n]+', text)` | one title per line |
| 2 | A line is "all capitals" if making it upper case changes nothing | `all_caps = line.upper() == line` | `THE LORD OF THE RINGS` -> `The Lord of the Rings` |
| 3 | The line is split at every single whitespace character, and the whitespace is kept | `regex.split(r'(\s)', line)` | `two  spaces` -> `Two  Spaces` |
| 4 | In an all-capitals line, initials are kept | `UC_INITIALS` | `J.R.R. TOLKIEN` -> `J.R.R. Tolkien` |
| 5 | `d'`, `o'`, `l'` words: third letter capital; first letter capital only for `o` | `APOS_SECOND` | `o'brien and d'artagnan` -> `O'Brien and d'Artagnan` |
| 6 | `Mc` words: `Mc` plus the rest as its own title | `MAC_MC` | `mcdonald and McGregor` -> `McDonald and McGregor` |
| 7 | `mr`, `mrs`, `ms`, `dr`: first letter capital, rest untouched | `MR_MRS_MS_DR` | `mr smith and dr jones` -> `Mr Smith and Dr Jones` |
| 8 | A dot between two word characters: word untouched | `INLINE_PERIOD` | `visit example.com now` -> `Visit example.com Now` |
| 9 | A capital after the first letter, when the line is not all capitals: word untouched | `UC_ELSEWHERE` | `iPhone vs. android` -> `iPhone vs. Android` |
| 10 | Small words become lower case: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. | `SMALL_WORDS` | `to be or not to be` -> `To Be or Not to Be` |
| 11 | A word with `/` but not `//`: each part is its own title | `"/" in word and "//" not in word` | `km/h a/b` -> `Km/H a/B` |
| 12 | A word with `-`: each part is its own title | `'-' in word` | `state-of-the-art design` -> `State-of-the-Art Design` |
| 13 | A word of consonants only (y does not count), longer than 2 letters: all capitals | `CONSONANTS` | `hmm nth st tv` -> `HMM NTH St Tv` |
| 14 | Otherwise the first word character after leading punctuation becomes a capital | `CAPFIRST` | `(of mice)` -> `(Of Mice)` |
| 15 | A small word as first word of the line gets a capital | `SMALL_FIRST` | `a tale of two cities` -> `A Tale of Two Cities` |
| 16 | A small word as last word gets a capital, also with one punctuation mark after it | `SMALL_LAST` | `stand by.` -> `Stand By.` |
| 17 | A small word after a sub-phrase mark and a space gets a capital | `SUBPHRASE` | `rise: the fall` -> `Rise: The Fall` |

## 5. Surprises

Inputs whose real output was not what a reader expects. These are the rare paths the tests aim at.

| Input | Output | Rule behind it |
|---|---|---|
| `nasa and the fbi` | `Nasa and the Fbi` | lower-case acronyms are not restored |
| `NASA and the FBI` | `NASA and the FBI` | 9 |
| ` the end` (leading space) | ` the End` | the first word is empty, so 15 finds nothing |
| `going in ` (trailing space) | `Going in ` | the last word is empty, so 16 finds nothing |
| `the x-RAY machine` | `The X-Ray Machine` | 12: the part `RAY` alone is an all-capitals line |
| `the RAY machine` | `The RAY Machine` | 9 |
| `O'BRIEN AND SONS` | `O'BRIEN and Sons` | 5 runs before the lower-casing of an all-capitals line |
| `MRS SMITH AND DR JONES` | `MRS Smith and DR Jones` | 7 leaves the rest of the word untouched |
| `D'OH` | `d'OH` | 5: `d` is made lower case |
| `Mcx rules` | `MCX Rules` | too short for 6, then 13 |
| `mcd` | `MCD` | 13 |
| `the mcthe saga` | `The McThe Saga` | 6: the rest of a `Mc` word is a title of its own, so 15 applies to it |
| `xyz corp` | `Xyz Corp` | y is not a consonant |
| `the u.s.a. today` | `The u.s.a. Today` | 8 |
| `version v2.0 is out` | `Version v2.0 Is Out` | 8: digits are word characters |
| `ph.d. thesis` | `ph.d. Thesis` | 8, also for the first word |
| `a.b c` | `A.b C` | 8, then 15 capitalises the `a` |
| `x: anVil` | `X: AnVil` | 17 matches the start of a longer word |
| `at&t and q&a` | `At&t and Q&A` | 16 sees `a` after `&` as the last small word |
| `the time q&a?` | `The Time Q&A?` | 16 with one mark after the small word |
| `the time q&a?!` | `The Time Q&a?!` | 16 allows only one mark |
| `and/or either/or` | `And/or Either/Or` | 11, then 15 and 16 |
| `x/iPhone-case sale` | `X/iPhone-case Sale` | 11 before 12: the part `iPhone-case` is kept by 9 |
| `a/mcx-y road` | `A/McX-Y Road` | 11 before 12: the part `mcx-y` is a `Mc` word |
| `//host/path here` | `//Host/path Here` | `//` blocks 11; 14 skips the slashes |
| `see http://example.com/a-b here` | `See http://example.com/a-b Here` | 8 |
| `#the end` | `#The End` | 14 and 15: `#` is in the punctuation list |
| `^the end` | `^the End` | `^` is not in the punctuation list |
| `one <two three` | `One <two Three` | `<` is not in the punctuation list |
| `_the end` | `_The End` | `_` is a word character and is also in the punctuation list |
| `the end w&of_` | `The End W&Of_` | 16: `_` counts as the one mark |
| `the end w&of^` | `The End W&of^` | `^` does not |
| `one -the two` | `One -the Two` | no space after the dash, so 17 does not apply |
| `the nth, degree` | `The Nth, Degree` | the comma switches 13 off |
| `__init__ method` | `__init__ Method` | `_` is a word character |
| `2nd time 3-d` | `2nd Time 3-D` | a digit is the first word character |

## 6. Rules the agent got wrong

Honest record of this build.

- The word rules were right at the first full comparison: 2000 of 2000 visible lines, 2000 of 2000 hidden
  lines, and 200,000 of 200,000 extra random titles (`dev/fuzz.py`) gave the same output as the original.
  What made that possible: the port keeps the order of the Python code line by line, works on characters and
  not on bytes, and copies the punctuation list and the small-word list from the source.
- What did go wrong, twice, was the build check. `go build ./...` gave 0 with the message
  `build output "titlecase" already exists and is a directory`: first because the empty Python package folder
  `titlecase/` was still in the repository after the `.py` files were deleted, then because a `__pycache__`
  folder had been copied into the image and kept that folder alive. `solution/solve.sh` now removes both.
- The first version of the hidden set was too weak. Of 115 deliberately broken ports (`dev/mutants.py`), it let
  29 through: ports with one character missing from the punctuation list, a port that handles the rest of a
  `Mc` word without the first-word rule, a port that splits at `-` before `/`, and a port that allows several
  marks after a small last word. `tests/gen.py` now builds titles for each of these, and the hidden set
  catches 114 of the 115. The last one has no effect on any output at all.

The rules that are easiest to get wrong, measured by how few hidden lines notice the mistake
(`dev/mutation_report.txt`): the place of `_` and `-` in the punctuation list, the punctuation before a small
first word, the space that must follow a sub-phrase mark, and the rule that a capital elsewhere keeps a word
only when the capital comes after at least one letter.

## 7. How the tests were tested

- `python tests/gen.py` twice gives identical files; each of the four files has 2000 lines.
- Oracle 1.0, do-nothing 0.0, cheat 0.1667 (Harbor 0.20.0, Reward Kit 0.2.4, image `golang:1.23`, Go 1.23.12).
- A program that only copies its input to its output, with the `.py` files deleted, would get 0.3633: 90 of
  the 2000 hidden titles are already right without any change.
- 115 broken variants of the port, one small change each: 114 change at least 3 hidden lines, 1 changes nothing
  anywhere.
