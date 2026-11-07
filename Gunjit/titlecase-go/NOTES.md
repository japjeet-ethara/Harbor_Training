# NOTES: titlecase-go

Author notes for the Harbor task. The agent never sees this file: it only gets
`instruction.md` and the container built from `environment/`.

## Source

| | |
|---|---|
| Repository | https://github.com/ppannuto/python-titlecase |
| Commit | `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05T22:03:59-07:00) |
| Version | 2.4.1 |
| Licence | MIT (`LICENSE.txt`, kept in the snapshot) |
| Snapshot | `environment/python-titlecase/`, made with `git archive`, no `.git` |

The function under test is `titlecase(text)` in `titlecase/__init__.py`, called with its
default arguments.

**Reference mode.** The original imports the optional `regex` package and falls back to `re`
with simpler patterns when it is missing. The two modes give different answers (95.5% of the
hidden titles agree, see "Baselines"). The frozen answers use the mode **with `regex`**
(`titlecase.REGEX_AVAILABLE is True`). The instruction says so, and the agent image has
`python3-regex` installed so the agent can run the same reference.

## The rules `titlecase()` applies

Each example was run against the original. A word is whatever sits between two whitespace
characters; the checks run in this order and the first one that matches wins.

| # | Rule | Example input | Output |
|---|---|---|---|
| 1 | Normal word: capitalise the first letter after any leading punctuation | `the lord of the rings` | `The Lord of the Rings` |
| 2 | Small words stay lower case (`a an and as at but by en for if in of on or the to v v. via vs vs.`) | `war and peace in our time` | `War and Peace in Our Time` |
| 3 | A small word is capitalised when it is the first or the last word | `something to be afraid of` | `Something to Be Afraid Of` |
| 4 | A small word is capitalised after `: . ; ? ! -` or a dash, followed by a space | `snakes on a plane - the tv edit` | `Snakes on a Plane - The Tv Edit` |
| 5 | A line that is entirely upper case is lower-cased first, then titlecased | `THIS IS ALL CAPS AND SHOULD BE ADDRESSED` | `This Is All Caps and Should Be Addressed` |
| 6 | In an all-caps line, upper-case initials are kept | `WASHINGTON, D.C. SHOULD BE FIXED` | `Washington, D.C. Should Be Fixed` |
| 7 | A word with a capital after its first letter is left alone (not in an all-caps line) | `iTunes should be unmolested` | `iTunes Should Be Unmolested` |
| 8 | A word with a dot between two letters is left alone | `this is just an example.com` | `This Is Just an example.com` |
| 9 | A word of 3 or more letters, all consonants (`y` is not one), becomes upper case | `words like cnn are acronyms` | `Words Like CNN Are Acronyms` |
| 10 | A word with `/` (but not `//`) is split and each part titlecased on its own | `a title and/or string` | `A Title and/or String` |
| 11 | A word with `-` is split and each part titlecased on its own | `end-to-end two-not-three` | `End-to-End Two-Not-Three` |
| 12 | `Mc`/`mc`/`MC` + 2 or more characters: `Mc` then the rest titlecased as its own title | `mcthe mcfoo-bar MCFOO-BAR` | `McThe McFoo-Bar McFoo-Bar` |
| 13 | `mr mrs ms dr` (any case): only the first letter is upper-cased | `mr mrs ms mss dr DR` | `Mr Mrs Ms MSS Dr DR` |
| 14 | `d' l' o'` + letters: `d`/`l` lower, `O` upper, next letter upper | `l'grange d'angelo O'GranGe` | `l'Grange d'Angelo O'GranGe` |
| 15 | A word that starts with a digit is left alone | `34th 3rd 2nd` | `34th 3rd 2nd` |
| 16 | Every whitespace character is kept exactly as it was | `two  spaces` | `Two  Spaces` |
| 17 | Letters are Unicode letters, not just A to Z | `EL NIÑO A ARRIVÉ HIER` | `El Niño a Arrivé Hier` |

## Traps: where a first guess is wrong

These are the cases the generator leans on. Each output is what the original really returns.

| Input | Output | Why it surprises |
|---|---|---|
| `st nd hmm tv` | `St Nd HMM Tv` | The consonant rule needs 3 letters; `tv` has 2 |
| `words like fbi` | `Words Like Fbi` | `i` is a vowel, so `fbi` is not "all consonants" |
| `tcp/ip` | `TCP/Ip` | The slash rule titlecases each part alone: `tcp` is all consonants, `ip` is not |
| `MR SMITH GOES TO NASA` | `MR Smith Goes to Nasa` | Rule 13 runs before the all-caps lower-casing, and all-caps destroys acronyms |
| `mr. and mrs. person` | `Mr. And Mrs. Person` | Rule 4 treats the dot of `mr.` as a sentence end |
| `x. v. a b` | `X. V. a B` | Rule 4 matches `. v.` and consumes the second dot, so `. a` is never seen |
| `vs. a b: vs. a` | `Vs. A B: Vs. A` | Here rule 4 matches only `v`, so the dot is still there for `. a` |
| ` the cat` | ` the Cat` | The first "word" is the empty string before the leading space |
| `the cat of ` | `The Cat of ` | Same at the end: the last word is empty |
| `in.a` | `In.A` | Kept by rule 8, then rule 3 fires twice on the same word |
| `to-do list to-do` | `To-Do List to-Do` | The "last word" pattern needs the small word at the very end of the word |
| `a-b the-the` | `A-B the-The` | Hyphen parts are titlecased without the first/last rule |
| `(u)rware and vapo(u)rware` | `(U)rware and Vapo(u)rware` | Capitalisation skips leading punctuation only |
| `mr mctavish went to macdonalds` | `Mr McTavish Went to Macdonalds` | Only `Mc` is special, `Mac` is not |
| `o'grange's o'as' o's'` | `O'Grange's O'As' O's'` | Rule 14 allows a 2-character tail made of `'` and `s` |
| `release notes for v1.2` | `Release Notes for V1.2` | A dot between a digit and a digit is not rule 8 (it is in the no-`regex` mode) |
| `at&t at&t` | `At&t At&t` | Lower-case input has no capital to protect it |

## What makes the task hard

- Go's `regexp` has no look-ahead, look-behind, back-references or Unicode-aware `\b`. The
  patterns `SMALL_FIRST`, `SMALL_LAST` and `SUBPHRASE` depend on the order the alternatives
  are tried and on what a match consumes, so they must be rebuilt by hand
  (`solution/port/main.go`).
- The rules interact: the order of the checks, recursion on `/`, `-` and `Mc` parts, and the
  all-caps flag being recomputed for every part.
- The reference mode has to be chosen correctly (with `regex`).
- A module named `titlecase` next to a leftover `titlecase/` folder makes `go build ./...`
  fail with "build output already exists and is a directory". The cheat hit this first. Running
  the original creates `titlecase/__pycache__`, so deleting only the `.py` files leaves that
  folder behind. The instruction requires `go build ./...` to pass, so this is a fair trap.

## Files

| Path | What it is |
|---|---|
| `instruction.md` | The only text the agent reads |
| `task.toml` | Timeouts, resources, non-root agent user, separate verifier, artifact hand-over |
| `environment/Dockerfile` | Pinned `golang:1.23` + python3 + python3-regex + the snapshot at `/workspace/repo` |
| `solution/solve.sh`, `solution/port/` | The oracle: installs the Go port, deletes every `.py` |
| `tests/gen.py` | Makes the titles and freezes the answers from the original (`random.seed(1)`) |
| `tests/data/` | `inputs.txt`/`expected.txt` (visible) and `hidden_inputs.txt`/`hidden_expected.txt` (graded) |
| `tests/Dockerfile`, `tests/test.sh` | The verifier image and entry point |
| `tests/checks/` | The three Reward Kit checks and `reward.toml` |
| `cheat/solve.sh` | A cheat that prints the visible answers, used to prove the tests catch it |
| `scripts/validate.py` | Runs oracle, nop and cheat through Harbor and checks the three rewards |
| `scripts/fuzz.py` | Compares a Linux build of the port with the original on random titles |

## Scoring

`reward = (1 × build + 1 × no_python + 4 × behaviour) / 6`

| Attempt | build | no_python | behaviour | reward |
|---|---|---|---|---|
| Nothing done | 0 | 0 | 0 | 0 |
| Go code that builds, `.py` files still there | 1 | 0 | 0 | 0.167 |
| Perfect port | 1 | 1 | 1 | 1 |

## Validation results

Run on 2026-11-06 with Harbor 0.25.0 and Docker Desktop on Windows (`python scripts/validate.py`):

| Run | build | no_python | behaviour | reward | Required |
|---|---|---|---|---|---|
| `oracle` (reference solution) | 1.0 | 1.0 | 1.0 | **1.0** | 1.0 |
| `nop` (does nothing) | 0.0 | 0.0 | 0.0 | **0.0** | 0.0 |
| cheat (prints the visible answers) | 1.0 | 0.0 | 0.0 | **0.1667** | below 0.2 |

Other checks:

- `python tests/gen.py` run twice gives byte-identical files; each file has 2,000 lines; the
  visible and hidden titles share no line.
- The original, run inside the agent image (Debian python3 3.11.2 + python3-regex),
  reproduces all 4,000 frozen answers.
- `harbor lint --select ALL` reports nothing.

## Baselines on the hidden set (behaviour share only)

| Wrong answer | Share of hidden titles matched |
|---|---|
| Echo the input unchanged | 0.013 |
| Python `str.title()` | 0.179 |
| Capitalise every word | 0.186 |
| The original run without `regex` | 0.955 |

## Decisions that differ from the training guide

- **The repo snapshot lives in `environment/python-titlecase/`**, because Docker can only
  copy from inside the build folder. `tests/gen.py` reads that snapshot (and checks its
  SHA-256) instead of `../python-titlecase`, so the task folder is complete on its own.
- **Reward Kit is installed in `tests/Dockerfile`**, not downloaded by `test.sh`, so grading
  needs no network. The checks live in `tests/checks/` so Reward Kit does not try to run
  `tests/gen.py` as a check, and they run one at a time (`--max-concurrent-programmatic 1`)
  because two of them build in the same folder.
- **`python3-regex` is in the agent image**, so the agent can run the same reference that
  froze the answers.
- **The `build` check also builds the root package into a program**, offline
  (`GOPROXY=off`, `GOFLAGS=-mod=mod`, `GOTOOLCHAIN=local`, `CGO_ENABLED=0`), and fails on a
  `require` or `replace` line in `go.mod`. Third-party source pasted in as a local package
  cannot be detected.
- **The submitted program is treated as untrusted.** The verifier has no network and no system
  Python; `/tests` and `/root` are readable by root only; the program runs as `nobody`, and
  anything it leaves running is killed before the reward is written. Without this a program
  could search the disk for the answer sheet.
- **Images are pinned by digest and the agent runs as the non-root user `agent`**
  (`harbor lint --select ALL` asks for both).

## Known limits

- The Go port matches the original on all 4,000 frozen titles and on 180,000 fuzzed titles
  in the same character set (`scripts/fuzz.py`, mode `narrow`). In mode `wide`, which adds
  unusual Unicode, the one known difference is that Python lower-cases a word-final Greek `Σ`
  to `ς` and Go to `σ`. The generator does not use Greek.
- Harbor copies the repository through the host on its way to the verifier, and that copy is
  best-effort. On a Windows host, symlinks or names differing only in case may not survive.
- An empty program plus deleting the `.py` files scores 0.333 (build and no_python pass,
  behaviour is 0). The guide's three checks allow this.

## To make the task harder

- Pay `build` and `no_python` only when `behaviour` is above a threshold, or use `all-pass`
  on a second reward, to close the 0.333 gap above.
- Add titles with characters whose upper/lower case differs between Python and Go
  (`ß`, `İ`, final `Σ`), after stating the wider character set in the instruction.
- Add property checks next to exact match (for example: the output has the same whitespace
  as the input).
