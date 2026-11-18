# NOTES: python-titlecase → Go (Harbor task `trainee/titlecase-go`)

## Source

| | |
|---|---|
| Repository | https://github.com/ppannuto/python-titlecase |
| Commit (SHA) | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` |
| Commit date | 2024-04-05T22:03:59-07:00 |
| Version | 2.4.1 |
| Licence | **MIT** (accepted: MIT / BSD / Apache) |
| Only code file that matters | `titlecase/__init__.py` (293 lines) |

**Reference behaviour = with the optional `regex` package installed** (`REGEX_AVAILABLE = True`).
Without it the library silently falls back to `re` with ASCII-only patterns, giving different answers
for non-ASCII input. Task data was generated with `regex 2026.11.15`, Python 3.12.

## The rules of `titlecase(line)` (default arguments)

Each example below was produced by running the original; none was typed from memory.

| # | Rule | Example (input → output) |
|---|---|---|
| 1 | Line is "all caps" if `line.upper() == line`. Then every word is lower-cased first, then capitalised. | `THE LORD OF THE RINGS` → `The Lord of the Rings` |
| 2 | Small words (`a an and as at but by en for if in of on or the to v v. via vs vs.`) are lower-cased. | `a tale of two cities` → `A Tale of Two Cities` |
| 3 | First word: a small word is capitalised, skipping leading punctuation. | `(the) quick fox` → `(The) Quick Fox` |
| 4 | Last word: a small word is capitalised, even with one trailing punctuation mark. | `what is it for.` → `What Is It For.` · `the end of the` → `The End of The` |
| 5 | Sub-phrases: after `: . ; ? !` or a dash + one space, a small word is capitalised. | `hello: the world` → `Hello: The World` |
| 6 | A word containing letter-`.`-letter is left untouched. | `visit example.com today` → `Visit example.com Today` |
| 7 | A word with an upper-case letter after its first letter is left untouched (unless the line is all caps). | `buy an iPhone or eBay item` → `Buy an iPhone or eBay Item` |
| 8 | `Mc`/`mc`/`MC` prefix: `Mc` + the rest titlecased recursively. | `mcdonald and MCDONALD` → `McDonald and McDonald` |
| 9 | `mr mrs ms dr` (any case): only the first letter is upper-cased, the rest is kept. | `mr smith meets dr jones and MRS brown` → `Mr Smith Meets Dr Jones and MRS Brown` |
| 10 | `d'x` / `o'x` / `l'x` (`'` or `‘`): the letter after the apostrophe is upper-cased; `d`/`l` stay lower, `o` is upper. | `d'artagnan and o'neil` → `d'Artagnan and O'Neil` |
| 11 | Words with `/` (not `//`) or `-` are split, each part titlecased on its own (no first/last rule), and re-joined. `/` is tested before `-`. | `up-to-date and/or client/server` → `Up-to-Date and/or Client/Server` |
| 12 | A word made only of ASCII consonants (not `aeiouy`) and longer than 2 letters is upper-cased. | `convert pdf to html` → `Convert PDF to HTML` |
| 13 | Normal word: upper-case the first letter, skipping leading punctuation from a fixed set. | `(hello) world` → `(Hello) World` |
| 14 | All-caps lines: initials such as `J.R.R.` are kept. | `J.R.R. TOLKIEN` → `J.R.R. Tolkien` |
| 15 | Whitespace (tabs, repeated spaces, NBSP) is preserved exactly; words are split on Unicode `\s`. | `the  lord⇥of␣the rings` → `The  Lord⇥of␣the Rings` |

## Surprises: where a naive reading predicts the wrong output (the rare cases to test)

| Input | Original returns | Why |
|---|---|---|
| `’hello’ world` | `’hello’ World` | The curly `’` `”` are **not** in `PUNCT` (only `“` `‘` are), so the first-letter rule finds no letter and does nothing. |
| `\u00a0the lord` / ` the lord` | `\u00a0the Lord` | A leading space makes the first "word" empty, so the first-word rule hits `''`, not `the`. |
| `foo: in.x` | `Foo: In.x` | `SUBPHRASE` has no `\b` and no `re.I`: it capitalises any lower-case *prefix* that is a small word, even in a word otherwise left untouched. |
| `mcon` | `McOn` | The recursive call keeps `small_first_last=True`, so `on` becomes `On`. |
| `MIKE O'NEIL AND D'ARCY` | `Mike O'NEIL and d'ARCY` | In all-caps mode the apostrophe rule only fixes characters 0 and 2; the rest stays upper-case, `d` goes lower. |
| `mr smith … MRS brown` | `… MRS Brown` | Rule 9 never lower-cases the tail. |
| `vs` (alone) | `Vs` | Small word, but first *and* last. |
| `UNICODE test of ÉCOLE` | `UNICODE Test of ÉCOLE` | Rule 7 is not limited to ASCII (`\p{Letter}`, `\p{Uppercase_Letter}`). |
| `l'été de la vie` | `l'Été De La Vie` | `de`/`la` are not in the small-word list. |
| `rock'n'roll for you` | `Rock'n'roll for You` | Only a leading `d' o' l'` triggers the apostrophe rule. |

Also found while porting (kept out of the data on purpose; see "Fairness"):

* `UC_INITIALS`'s `X.Y` branch is **dead code in practice**: any word it could match already
  contains letter-`.`-letter and is left alone by rule 6 (a mutation test confirms no output changes).
* Go's `regexp` has no Unicode `\b` and no `\p{…}` equivalent that matches `regex`'s classes
  exactly, so everything was re-implemented as rune code (see `solution/main.go`).
* Python's `\s` in the `regex` module is exactly Unicode `White_Space` (it does **not** include
  U+001C–U+001F, unlike `re`).

## Fairness: input alphabet

Test titles use ASCII, common punctuation, curly quotes/dashes, Latin-1 + Latin Extended-A letters and
Unicode spaces. They avoid characters whose Python `upper()/lower()` is multi-character or
context-dependent (`ß`, `ŉ`, `İ`, final sigma, ligatures …) because those would test Go's `unicode`
tables vs. Python's, not the porting skill. This scope is stated in `instruction.md`.

## Task layout

```
titlecase-go/
├── instruction.md             what the agent reads
├── task.toml                  settings, artifacts, network, separate verifier
├── environment/Dockerfile     golang:1.23.9-bookworm + python3/regex + the repo (no .git)
├── environment/python-titlecase/   the repo at the pinned SHA
├── solution/{solve.sh,main.go}     the oracle (Go port, then deletes every .py)
├── tests/                     verifier (separate container)
│   ├── Dockerfile  test.sh  reward.toml
│   ├── build.py  no_python.py  behaviour.py    one score each
│   └── data/{inputs,expected,hidden_inputs,hidden_expected}.txt
├── cheat/solve.sh             a "port nothing" cheat to prove the tests catch it
└── tools/                     author-only: gen.py, make_cheat.py, simulate.sh
```

`tools/gen.py` is **not** in `tests/` (as the PDF suggests) because Reward Kit executes every
top-level `tests/*.py` as a criteria file.

## Scoring

`reward = (1·build + 1·no_python + 4·behaviour) / 6` (weighted mean).

* `build`: `go build ./...` passes (binaries go to a temp dir so a module/directory name clash
  cannot fail a correct solution).
* `no_python`: build passes **and** no `.py` file anywhere.
* `behaviour`: share of the 2000 hidden lines that equal the original's answer byte for byte.
  The agent's program runs as an unprivileged user so it cannot read `/tests`.

## Validation results (see the chat summary for how they were run)

| Run | build | no_python | behaviour | **reward** |
|---|---|---|---|---|
| oracle | 1 | 1 | 1.0 | **1.0** |
| nop | 0 | 0 | 0 | **0.0** |
| cheat (replays visible answers, keeps .py) | 1 | 0 | 0.0 | **0.1667** |


## Task Reflection

- Rules the agent got wrong most often: [Mention the actual rules observed during evaluation.]
- To make the task harder: [Mention an additional challenge or edge case.]

