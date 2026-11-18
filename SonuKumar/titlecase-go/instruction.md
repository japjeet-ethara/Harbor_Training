# Repository

`/workspace/repo` contains the Python project `python-titlecase` (MIT license, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`), which implements John Gruber's titlecasing algorithm with enhancements by Stuart Colville and Patrick Pannuto. Its `titlecase()` function converts a line of text to title case according to English capitalization and style conventions. The Python source in the repository defines the authoritative reference behavior.

# What to build

Implement a command-line Go program in `/workspace/repo` using standard input and output:
- Read titles line-by-line from standard input (`stdin`).
- Strip the line terminator (`\n` or `\r\n`).
- Apply the default Python `titlecase()` behavior to each title line.
- Write each titlecased result line followed by `\n` to standard output (`stdout`).
- An empty input line produces an empty output line.
- Preserve the exact order of lines, and do not emit interactive prompts or extra output.

# Hard rules

- Use only the Go standard library; no external or third-party dependencies are permitted.
- `go build ./...` must succeed in `/workspace/repo`.
- No `.py` files may remain anywhere in `/workspace/repo` when finished.
- The Go program must not invoke external binaries or interpreters (no `os/exec`, no Python).

# Required Behaviour

For every input title, the Go program's output must match the original Python `titlecase()` function byte-for-byte when called with its default arguments (`callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, `normalise_space_characters=False`).

Key rules implemented by the reference:
- **Whitespace**: Preserve input whitespace within and around a title, including leading/trailing whitespace, tabs, and repeated spaces. Do not normalize whitespace separators.
- **Small Words**: Lowercase words in the small-words list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`).
- **First and Last Words**: Capitalize a small word if it is the first or last word of the title line. If the line begins with whitespace, the leading token is whitespace/empty, so a following small word is not at the first position and remains lowercase.
- **Subphrase Punctuation**: After `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, or `―` followed by a space, capitalize a following small word.
- **All-Uppercase Lines**: On an all-uppercase line, words that are not initialisms, apostrophe words, Mc names, honorifics, inline periods, small words, slashes, or hyphens are lowercased before standard title-casing. Dotted uppercase initials (e.g. `U.S.`) are preserved.
- **Inline Periods**: Words containing a letter-period-letter pattern (such as domains `example.com` or dotted words `e.g.`) remain unchanged. On non-uppercase lines, words with internal uppercase letters (e.g. `iPhone`, `eBay`) are preserved.
- **Apostrophe Contractions and Prefixes**: For words matching `^[dol]['‘]\w+('s)?$`, capitalize the letter following the apostrophe. Lowercase the initial letter for a consonant prefix (`d'`, `l'`) and uppercase it for a vowel prefix (`o'`).
- **Mc Names**: For words starting with `mc`, `Mc`, or `MC` (case-insensitive) followed by letters, rewrite the prefix as `Mc` and recursively titlecase the remainder with first/last capitalization enabled.
- **Honorifics**: For `Mr`, `Mrs`, `Ms`, or `Dr` (case-insensitive), uppercase only the initial character and leave remaining characters unchanged.
- **Slash and Hyphen Compounds**: Recursively titlecase slash-delimited parts (when the word contains `/` but not `//`) and hyphen-delimited parts (`-`), with first/last small word capitalization disabled during recursion.
- **Acronyms**: If a word consists entirely of ASCII consonants (excluding `a, e, i, o, u, y`) and is longer than two characters, convert it to all-uppercase as an acronym.
- **Standard Words**: Capitalize the first letter of ordinary words after any leading punctuation.

# Not checked

Execution speed, memory footprint, and exact error message formatting are not graded. The program must process 2000 lines within standard evaluation timeouts.

# Grading

Automated grading assigns scores across build success (`build`), removal of Python source files (`no_python`), and byte-identical correctness on a hidden evaluation set (`behaviour`).
