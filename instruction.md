# Repository

The original project is a Python implementation of John Gruber's titlecase algorithm. Its `titlecase()` function converts text to title case while preserving selected capitalization, punctuation, separators, and small-word rules. The default small-word list follows the New York Times style list and also includes `v` and `vs`.

# What to build

Implement a Go program in `/workspace/repo` using only its standard input and output: read exactly one title per input line, remove the line terminator (`\n` or `\r\n`), apply the default Python `titlecase()` behavior to that title, and write exactly one result line to standard output. Emit an empty output line for an empty input line, preserve input order, and do not print prompts or other output.

# Hard rules

- Use only the Go standard library; do not add third-party dependencies.
- No `.py` files may remain anywhere in the repository.
- `go build ./...` must pass.

# Behaviour

For every input title, output must match the original Python `titlecase()` byte-for-byte. The stdin program uses the Python function's defaults: no callback, `small_first_last=True`, `preserve_blank_lines=False` (irrelevant when processing one line at a time), and `normalise_space_characters=False`.

- Preserve every input whitespace character within a title, including leading/trailing whitespace, tabs, and repeated spaces.
- On an all-uppercase line, lowercase ordinary words before processing; preserve dotted uppercase initials matching the original initialism rule.
- Lowercase these small words when they are not at a phrase boundary: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `via`, and `vs`, with the optional periods supported by the original patterns. Capitalize a small word at the first or last phrase position.
- After `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, or `―` followed by a space, capitalize a following small word.
- Capitalize the first letter of an ordinary word after any leading punctuation recognized by the original implementation.
- Preserve words containing a letter-period-letter sequence. On a non-uppercase line, also preserve words with uppercase letters elsewhere when they match the original mixed-case rule.
- For words matching the original apostrophe pattern beginning with `d'`, `l'`, or `o'`, capitalize the letter after the apostrophe; lowercase the initial letter for a consonant start and uppercase it for a vowel start.
- For a word beginning with `Mc` or `MC`, output a capitalized `Mc` prefix and recursively titlecase the remainder. For `Mr`, `Mrs`, `Ms`, or `Dr` (case-insensitive), uppercase only the first character and leave the remaining characters unchanged.
- Recursively titlecase slash-separated parts when the word contains `/` but not `//`. Recursively titlecase hyphen-separated parts as well; recursive calls do not capitalize first/last small words.
- If a word consists only of ASCII letters from `bcdfghjklmnpqrstvwxz` and has more than two characters, uppercase it as an acronym.
- Preserve the original whitespace separators; do not normalize them.

# Not checked

Speed, memory usage, and error message wording are not checked.

# Grading

Hidden automatic grading provides partial credit based on how accurately the program implements the required behavior.
