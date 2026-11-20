# Task notes: sanyam/titlecase-go

Author: Sanyam Sehrawat. These are the author's working notes; the agent only ever sees
`instruction.md` and the container.

## 1. Source project

| | |
|---|---|
| Repository | https://github.com/ppannuto/python-titlecase |
| Commit | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` |
| Commit date | 2024-04-05T22:03:59-07:00 |
| Version | 2.4.1 (`__version__` in `titlecase/__init__.py`) |
| Licence | MIT (`LICENSE.txt`, copyright Patrick William Pannuto) |
| Snapshot | `environment/python-titlecase/`, produced with `git archive HEAD` (no `.git`) |

The function under test is `titlecase(text)` with default arguments. It imports the
third-party `regex` package when present and falls back to `re` with weaker patterns when
it is not. The two modes disagree on some inputs (for example `v1.2`), so the task fixes
the mode: **with `regex`** (`REGEX_AVAILABLE == True`). The agent image installs
`python3-regex` so the agent can run the very same reference.

## 2. What `titlecase()` does, rule by rule

A "word" is a run of characters between whitespace characters; every whitespace
character is kept. For each word the checks below run in this order and the first one
that applies wins. Every example was produced by running the original.

| # | Rule | Input | Output |
|---|---|---|---|
| 1 | In a line typed entirely in capitals, words made of initials (`D.C.`) are kept | `WASHINGTON, D.C. IN THE MORNING` | `Washington, D.C. In the Morning` |
| 2 | `d'`, `l'`, `o'` + letters: `d`/`l` stay lower, `O` goes upper, the letter after the apostrophe goes upper | `o'neil d'artagnan l'amour` | `O'Neil d'Artagnan l'Amour` |
| 3 | `mc`/`Mc`/`MC` + a word: `Mc` followed by the rest titlecased as a line of its own | `mcdonald MCDONALD mcfoo-bar` | `McDonald McDonald McFoo-Bar` |
| 4 | `mr`, `mrs`, `ms`, `dr` in any case: only the first letter is upper-cased | `mr mrs ms dr DR mss` | `Mr Mrs Ms Dr DR MSS` |
| 5 | A word with a dot between two letters is left alone | `visit example.com today` | `Visit example.com Today` |
| 6 | A word with a capital after its first letter is left alone (unless the whole line is capitals) | `iTunes should be left alone` | `iTunes Should Be Left Alone` |
| 7 | Small words are lower-cased: `a an and as at but by en for if in of on or the to v v. via vs vs.` | `war and peace in our time` | `War and Peace in Our Time` |
| 8 | A word containing `/` (but not `//`) is split and each part titlecased alone | `tcp/ip and/or http://a.b` | `TCP/Ip and/or http://a.b` |
| 9 | A word containing `-` is split and each part titlecased alone | `end-to-end to-do a-b` | `End-to-End to-Do a-B` |
| 10 | A line typed entirely in capitals is lower-cased first | `THIS IS ALL CAPS AND SHOULD BE FIXED` | `This Is All Caps and Should Be Fixed` |
| 11 | Three or more letters that are all consonants (`y` does not count) become an acronym | `words like cnn are acronyms` | `Words Like CNN Are Acronyms` |
| 12 | Otherwise the first letter after any leading punctuation is upper-cased | `(u)rware and vapo(u)rware` | `(U)rware and Vapo(u)rware` |
| 13 | The first and the last word of the line are capitalised even if small | `something to be afraid of` | `Something to Be Afraid Of` |
| 14 | A small word after `: . ; ? !` or a dash and a plain space is capitalised | `snakes on a plane - the tv edit` | `Snakes on a Plane - The Tv Edit` |
| 15 | Words starting with a digit are left alone | `3rd 42nd 1990s` | `3rd 42nd 1990s` |
| 16 | Letters are Unicode letters | `EL NIÑO A ARRIVÉ HIER` | `El Niño a Arrivé Hier` |
| 17 | Whitespace is preserved character for character | `two  spaces<TAB>and<NBSP>tabs` | `Two  Spaces<TAB>and<NBSP>Tabs` |

## 3. Surprises (the cases a first attempt gets wrong)

Each output is what the original really returns. The generator leans on these.

| Input | Output | Why |
|---|---|---|
| `st nd hmm tv` | `St Nd HMM Tv` | Rule 11 needs three letters; `tv` and `st` have two |
| `words like fbi are not` | `Words Like Fbi Are Not` | `i` is a vowel, so `fbi` is not an acronym |
| `tcp/ip` | `TCP/Ip` | Each side of the slash is judged alone |
| `MR SMITH GOES TO NASA` | `MR Smith Goes to Nasa` | Rule 4 fires before the all-caps lower-casing; `NASA` is lost |
| `mr. and mrs. person` | `Mr. And Mrs. Person` | Rule 14 sees `mr.` as the end of a sentence |
| `x. v. a b` | `X. V. a B` | Rule 14 consumes `. v.` including its dot, so `. a` is never seen |
| `vs. a b: vs. a` | `Vs. A B: Vs. A` | Here only `v` is consumed, the dot stays and `. a` matches |
| ` the cat` | ` the Cat` | The first word is the empty string before the leading space |
| `the cat of ` | `The Cat of ` | Likewise the last word is empty |
| `in.a` | `In.A` | Kept by rule 5, then rule 13 fires twice on the same word |
| `to-do list to-do` | `To-Do List to-Do` | The hyphen parts are titlecased without rule 13 |
| `a-b the-the` | `A-B the-The` | Same; only the whole word is first/last, not its parts |
| `at&t AT&T` | `At&t AT&T` | Lower case has no capital to protect it (rule 6) |
| `release notes for v1.2` | `Release Notes for V1.2` | A dot between digits is not rule 5 (it is in the no-`regex` mode) |
| `straße STRAßE` | `Straße STRAßE` | Python's `upper()` of `ß` is `SS`, so `STRAßE` is not "all caps" |
| `ﬁsh` | `FIsh` | `upper()` of the `ﬁ` ligature is two letters |
| `¿que? ¡hola!` | `¿que? ¡hola!` | `¿` and `¡` are not in the punctuation list, so nothing is capitalised |
| `o'grange's o'as' o's'` | `O'Grange's O'As' O's'` | Rule 2 allows a two-character tail made of `'` and `s` |

## 4. Why the port is hard

- Go's `regexp` has no look-around, no back-references, no Unicode-aware `\b`, and no
  ordered alternation with backtracking. `SMALL_FIRST`, `SMALL_LAST` and `SUBPHRASE`
  depend on which alternative is tried first and on what the match consumes (`v\.?`
  before `vs\.?`), so each one has to be rebuilt as explicit rune scanning.
- Python string methods are not Go's: `upper()` of `ß` or `ﬁ` is several characters,
  `lower()` of `İ` is two, `capitalize()` title-cases the first character. The all-caps
  test (`line.upper() == line`) inherits all of this.
- The rules interact: recursion on `/`, `-` and `Mc` parts recomputes the all-caps flag
  per part; the `Mc` tail is titlecased **with** the first/last rule, the hyphen and slash
  parts **without** it.
- `\w` and `\s` of the `regex` module are Unicode classes; `\s` is exactly Go's
  `unicode.IsSpace`, `\w` is letters, marks, decimal digits, connector punctuation, letter
  numbers, other alphabetic symbols and the two joiners.
- Choosing the wrong reference mode (without `regex`) silently costs about 5 % of the
  titles.

## 5. Files

| Path | Role |
|---|---|
| `instruction.md` | The only text the agent gets |
| `task.toml` | Timeouts, resources, separate offline verifier, `/workspace/repo` hand-over |
| `environment/Dockerfile` | `golang:1.23` (digest-pinned) + `python3` + `python3-regex`, snapshot at `/workspace/repo` |
| `solution/solve.sh`, `solution/src/` | The oracle: installs the Go port, deletes the Python package |
| `tests/gen.py` | Builds 2 × 2000 titles and freezes the answers by running the original (`random.seed(1)`) |
| `tests/data/sample/` | `titles.txt` + `answers.txt`, may be looked at |
| `tests/data/graded/` | `titles.txt` + `answers.txt`, the ones that count |
| `tests/Dockerfile`, `tests/test.sh`, `tests/grade.py` | Verifier image, entry point and the three checks |
| `cheat/solve.sh` | Prints the sample answers; proves the grader is not fooled |
| `scripts/validate.py` | Runs oracle, nop and cheat through Harbor and checks the rewards |
| `scripts/fuzz.py`, `scripts/compare.sh` | Compare the Go port with the original on random titles / the frozen sets |

## 6. Grading

`reward = (1 · build + 1 · no_python + 4 · behaviour) / 6`, computed by `tests/grade.py`,
written to `/logs/verifier/reward.json` on every code path.

| Situation | build | no_python | behaviour | reward |
|---|---|---|---|---|
| Nothing done | 0 | 0 | 0 | 0 |
| Go code that builds, Python still there | 1 | 0 | 0 | 0.1667 |
| Builds, Python deleted, wrong output | 1 | 1 | 0 | 0.3333 |
| Perfect port | 1 | 1 | 1 | 1 |

`no_python` and `behaviour` are only computed when the build passed, so deleting files
without writing a program earns nothing.

Design choices:

- **Separate, offline verifier.** The tests never enter the agent container; Harbor copies
  `/workspace/repo` into the verifier container (`artifacts` in `task.toml`). The verifier
  has no network and no `regex` package, so the program cannot call the original.
- **The program is treated as hostile.** It runs as `nobody`, with only its standard input,
  while `/tests` (which holds the answers) is `chmod 700` root. Anything it leaves running
  is killed. A program that tried to find the answer sheet on disk would see nothing.
- **Standard-library check** is textual (`require`/`replace` in `go.mod`) plus an offline
  build (`GOPROXY=off`). Third-party code pasted into the module cannot be detected.
- **Plain Python grader, no framework.** `grade.py` has no dependencies, so the verifier
  image is just Go + `python3` and grading needs no download.

## 7. Results

Harbor 0.25.0, Docker Desktop on Windows, 2026-11-16, `python scripts/validate.py`:

| Trial | build | no_python | behaviour | reward | Required |
|---|---|---|---|---|---|
| oracle | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 |
| nop | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| cheat | 1.0 | 0.0 | 0.0 | **0.1667** | below 0.2 |

Screenshots of the three reward pages are in `screenshots/`.

Other checks:

- `python3 tests/gen.py` run twice gives identical files; 2000 lines each; the sample
  and graded sets share no title.
- The Go port agrees with the original on all 4000 frozen titles and on 120,000 fuzzed
  titles (`scripts/fuzz.py`, 60,000 in `narrow` mode and 60,000 in `wide` mode, which adds
  random runs of unusual Latin letters, symbols and whitespace).
- `harbor lint . --select ALL` reports nothing.

## 8. What was hardest to get right, and how to make the task harder

Rules that needed the most care in the port: the first/last small-word rules and the
sub-phrase rule (alternation order and what the match consumes, see `x. v. a b`), the
all-caps test with Python's multi-character `upper()` (`ß`, `ﬁ`), and the `Mc` recursion
re-running the whole line logic on the tail.

Known limit: Python lower-cases a Greek capital sigma at the end of a word to `ς`, Go to
`σ`. The generator uses no Greek, and the instruction's character set excludes it.

To make the task harder: (a) gate `build` and `no_python` on `behaviour` being above a
threshold, closing the 0.3333 "empty program" gap; (b) add Greek and Turkish letters
(final sigma, dotted İ) to the stated character set; (c) add titles with `\x85`, ` `
and other exotic separators so the agent must learn exactly which characters split words.
