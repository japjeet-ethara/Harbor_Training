# Task: Port python-titlecase to Go

## Repository

The directory `/workspace/repo` contains [python-titlecase](https://github.com/ppannuto/python-titlecase), a Python library that converts strings to title case following the rules of the New York Times Manual of Style. Answers come from titlecase WITHOUT regex (canonical logic in standard `re` mode from `titlecase/__init__.py`, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`).

## What to Build

Write a Go program in `/workspace/repo` that reads one title per line from **stdin** and prints the titlecased result to **stdout**, one per line. The program must be a complete, buildable Go module (with `go.mod`).

## Hard Rules

1. **Go standard library only** — no third-party modules or external dependencies.
2. **No Python files may remain** — delete every `.py` and `.pyc` file anywhere under `/workspace/repo` when you are done.
3. **`go build ./...` must succeed** — the code must compile without errors.

## Behaviour

The Go program's output must match the original Python `titlecase()` function **byte for byte** for every input line. The canonical reference is `titlecase/__init__.py`. In summary, the rules are:

- **Small words:** Words in the small words list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`) stay lowercase unless they are the first or last word of the title.
- **First and last words:** The first and last words of the line are always capitalized, even if they are small words.
- **Sub-phrase capitalization:** When one of `:`, `.`, `;`, `?`, `!`, `-`, `–` (U+2013), `‒` (U+2012), `—` (U+2014), or `―` (U+2015) is followed by a single space and a small word, that small word is capitalized.
- **Mixed case (camelCase, etc.):** Words with uppercase letters after the first character (e.g. `iPhone`, `eBay`) are preserved, unless the entire line is all-caps.
- **Inline periods:** Words with letters immediately on both sides of a period (e.g. `e.g.`, `example.com`) are preserved.
- **Initialisms / UC Initials:** Uppercase initials with periods (e.g. `A.B.` or `A.B.C.`) are preserved, including on all-caps lines.
- **Apostrophe-second words:** Words matching prefixes `d'`, `o'`, or `l'` (regex `^[dol]['‘]\p{Letter}+`): if the initial letter is a consonant (`d'`, `l'`), it is lowercased (`d'Artagnan`, `l'Oreal`); if a vowel (`o'`), it is uppercased (`O'Brien`). The letter following the apostrophe is capitalized.
- **Mc prefix:** Names starting with `Mc` or `mc` capitalize the `Mc` prefix and recursively titlecase the remainder (e.g. `mcdonald` becomes `McDonald`). Note: The library does **not** match `Mac`.
- **Honorifics:** `Mr`, `Mrs`, `Ms`, `Dr` capitalize the first letter only.
- **Hyphenated & slash compounds:** Each segment of a word separated by `-` or `/` (except `//` URLs) is titlecased independently.
- **All-consonant acronyms:** Words longer than 2 characters composed entirely of ASCII consonants (excluding `y`: `bcdfghjklmnpqrstvwxz`) are uppercased (e.g. `nfl` becomes `NFL`). Note: `y` is treated as a vowel by the library, so words containing `y` (like `sync` or `rhythm`) are not acronym-uppercased.
- **All-caps lines:** If an entire line is uppercase (`line.upper() == line`), words are lowercased before titlecasing rules are applied (preserving `UC_INITIALS` like `A.B.`).

**Important:** Go's standard `regexp` package does not support look-around assertions or back-references. You must implement or adapt those behaviours using plain string and rune scanning logic.

## Not Checked

- Execution speed or memory usage.
- Error message wording.
- Code style or comments.

## Grading

Your solution will be graded automatically by hidden tests. Partial credit is awarded: the score is the fraction of test lines your program gets exactly right.
