# Titlecase Go Port

## Repository Description
The repository contains a Python implementation of `titlecase` (located in `titlecase/__init__.py`), which transforms input text into title case according to style conventions based on the New York Times Manual of Style. The Python source code of the `titlecase` function and its helper functions in the repository, as it exists at the start of the task, is the single source of truth for all transformation behaviour. Where any prose description and the Python source disagree, the Python source wins. You must read the Python source code in the repository before writing any Go code, and copy the exact behaviour of the version of the code present in the repository at the start of the task—including its regular expressions, constant word lists, and transformation order—rather than inferring behaviour from high-level summaries.

## What to Build
You must implement an executable Go program located in `/workspace/repo`. The `main` package must reside at the repository root (`/workspace/repo`), compiling to an executable binary that can be run directly from that directory. The program must read input line by line from standard input (`stdin`) and write the titlecased output line by line to standard output (`stdout`).

## Input/Output Contract
1. **Input stream:** Input MUST be read from standard input (`stdin`).
2. **Line delineation:** A line is defined as the sequence of bytes preceding a `\n` character.
3. **Line endings:** If a line ends with `\r\n`, the carriage return (`\r`) MUST be stripped before titlecasing, ensuring that CRLF (`\r\n`) and LF (`\n`) inputs yield byte-identical output.
4. **Final line without newline:** If the input stream terminates without a trailing `\n` on the final line, the program MUST process that line and write the titlecased output followed by `\n`.
5. **Empty lines:** An input line consisting of zero bytes before `\n` MUST produce an empty line on standard output (`stdout`) consisting of a single `\n`.
6. **Whitespace handling:** The program MUST reproduce the same split and join behaviour as the Python source (`regex.split(r'(\s)', line)` interleaved back with processed words), preserving all leading, trailing, and inter-word whitespace characters.
7. **Line length:** The program MUST process input lines of arbitrary length without failing, truncating, or erroring on lines that exceed fixed buffer sizes (such as the default 64 KiB buffer limit of Go's `bufio.Scanner`).
8. **Output destination:** Each titlecased line MUST be written to standard output (`stdout`) followed by exactly one `\n`.
9. **No extraneous output:** The program MUST NOT write banners, prompts, debugging logs, or diagnostic text to `stdout`. All diagnostics and error messages, if any, MUST be written exclusively to standard error (`stderr`).
10. **Character encoding:** Input MUST be processed as UTF-8. Non-ASCII characters (including accented letters, dashes, and curly quotes) MUST be handled according to Unicode character classes matching Python's `str` handling.
11. **Exit code:** The program MUST exit with status code `0` upon reaching end-of-file (`EOF`) on `stdin`.

## Hard Rules
- **Standard library only:** The Go program MUST NOT use any external dependencies, third-party packages, or vendored modules. The program MUST use only the Go standard library.
- **Valid go.mod:** The repository root `/workspace/repo` MUST contain a valid `go.mod` file. The `go.mod` file MUST NOT contain any `require` directives.
- **Offline compilation:** The program MUST NOT require network access to compile or execute.
- **Successful build:** Executing `go build ./...` from `/workspace/repo` MUST succeed with exit code `0`.
- **Absolute prohibition of Python files:**
  - The repository MUST NOT contain any files ending in `.py` (case-insensitive) anywhere within `/workspace/repo` or any of its subdirectories upon task completion.
  - This prohibition includes `setup.py`, `conftest.py`, all `__init__.py` files, test files, and any vendored copies.
  - The agent MUST NOT retain Python source code by renaming `.py` files to other file extensions; non-Python files may remain only if they do not contain Python source code.
  - You may read the existing Python source files for reference during development, but you MUST delete every Python file before finishing the task.
  - The absence of all `.py` files across the entire repository is explicitly checked at the end of grading.

## Behaviour
The Go program's output MUST match the original Python `titlecase()` output byte for byte for every input. The Python reference implementation in `titlecase/__init__.py` at the start of the task is the single source of truth, evaluated in standard-library `re` fallback mode (WITHOUT the optional third-party `regex` package, `REGEX_AVAILABLE = False`). All reference answers come from titlecase WITHOUT regex.

The Go implementation must apply transformation rules in the exact order enforced by the Python reference implementation. That order is binding:

### Line Splitting
A line is split using the same split behaviour as the Python source: `regex.split(r'(\s)', line)`, where words are taken from even indices and whitespace tokens from odd indices. The boolean flag `all_caps` is computed as `line.upper() == line` using Unicode uppercase mappings.

### Word-Level Rules (Applied to Each Whitespace-Delimited Word)
Words are evaluated against the following rules in strict order; the first matching rule handles the word:
1. **Initials on all-caps line:** If `all_caps` is true and the word matches `UC_INITIALS` (`^(?:[\p{Uppercase_Letter}]{1}\.{1}|[\p{Uppercase_Letter}]{1}\.{1}[\p{Uppercase_Letter}]{1})+$`, with Unicode uppercase letters `\p{Lu}` and literal dots), the word is appended unchanged.
2. **Apostrophe prefix:** If the word matches `APOS_SECOND` (`^[dol]{1}['‘]{1}[\p{Letter}]+(?:['s]{2})?$`, case-insensitive, with ASCII prefix `d`, `o`, or `l`, straight quote `'` or curly quote `‘`, Unicode letters `\p{L}`, and optional trailing `'s`):
   - If the first character is an ASCII consonant (`d` or `l`, checked via `word[0] not in 'aeiouAEIOU'`), the first character is lowercased, the apostrophe is retained, the character immediately following the apostrophe is uppercased, and the remainder is retained (`word[0].lower() + word[1] + word[2].upper() + word[3:]`).
   - If the first character is the ASCII vowel `o`, the first character is uppercased, the apostrophe is retained, the character immediately following the apostrophe is uppercased, and the remainder is retained (`word[0].upper() + word[1] + word[2].upper() + word[3:]`).
3. **Mac/Mc prefix:** If the word matches `MAC_MC` (`^([Mm]c|MC)(\w.+)`, where `\w` is a Unicode word character `[\p{L}\p{N}_]` and `.+` matches at least one additional character), the prefix is capitalized as `Mc` (`match.group(1).capitalize()`) and concatenated with the recursive titlecase result of the remainder with `small_first_last=True`.
4. **Honorifics:** If the word matches `MR_MRS_MS_DR` (`^((m((rs?)|s))|Dr)$`, case-insensitive against the ASCII tokens `mr`, `mrs`, `ms`, and `dr`), the first character is uppercased and the remainder is left unchanged (`word[0].upper() + word[1:]`).
5. **Inline period or existing internal uppercase:** If the word contains an inline period matching `INLINE_PERIOD` (`[\p{Letter}][.][\p{Letter}]`, case-insensitive, with Unicode letters `\p{L}` surrounding a literal dot), OR if `all_caps` is false and the word matches `UC_ELSEWHERE` (`[%s]*?[\p{Letter}]+[\p{Uppercase_Letter}]+?` where `%s` is `PUNCT`), the word is appended unchanged.
6. **Small words:** If the word matches `SMALL_WORDS` (`^(a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?)$`, case-insensitive against the ASCII small-words list), it is converted entirely to lowercase.
7. **Slash-separated compounds:** If the word contains `/` and does not contain `//`, it is split on `/`; each part is recursively titlecased with `small_first_last=False`, and the parts are rejoined with `/`.
8. **Hyphen-separated compounds:** If the word contains `-`, it is split on `-`; each part is recursively titlecased with `small_first_last=False`, and the parts are rejoined with `-`.

### Pre-processing Step (All-Caps Lowering)
If none of rules 1–8 matched and `all_caps` is true, convert the word to lowercase (`word = word.lower()`) before evaluating the remaining word rules below.

### Remaining Word-Level Rules
9. **Consonant acronyms:** If the word consists entirely of ASCII consonants (`b-df-hj-np-tv-z`, case-insensitive, derived from `set(string.ascii_lowercase) - {'a', 'e', 'i', 'o', 'u', 'y'}`) matching `\A[b-df-hj-np-tv-z]+\Z` and has a length strictly greater than 2, the word is converted entirely to uppercase. Non-ASCII letters MUST NOT be counted as consonants under this rule.
10. **Default first-letter capitalization:** Otherwise, the first Unicode letter matching `CAPFIRST` (`^[%s]*?([\p{Letter}])` where `%s` is `PUNCT`) is converted to uppercase while leading punctuation and subsequent characters are preserved unchanged.

### Line-Level Rules (Applied After Word Processing)
After all words in a line are processed, the following line-level steps are applied in order:
1. **Reassembly:** Interleave the processed words and original whitespace tokens back into a single line string using the same split and join behaviour as the Python source (`line_to_be_joined[::2] = tc_line; line_to_be_joined[1::2] = spaces; result = "".join(line_to_be_joined)`).
2. **First small word capitalization:** If `small_first_last` is true and the line contains words, capitalize the small word at the start of the line matching `SMALL_FIRST` (`^([%s]*)(%s)\b` where `%s` represents `PUNCT` and `SMALL`).
3. **Last small word capitalization:** If `small_first_last` is true and the line contains words, capitalize the small word at the end of the line matching `SMALL_LAST` (`\b(%s)[%s]?$` where `%s` represents `SMALL` and `PUNCT`).
4. **Sub-phrase small word capitalization:** Any small word following sub-phrase punctuation matching `SUBPHRASE` (`([:.;?!\-–‒—―][ ])(%s)` where `%s` represents `SMALL`) has its small-word portion capitalized.

### Regular Expression and Parser Semantics
The constants from the Python source are:
- `SMALL`: `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?` (ASCII small words)
- `PUNCT`: `!"“#$%&'‘()*+,\-–‒—―./:;?@[\\\]_\`{|}~` (ASCII punctuation plus Unicode characters `“` U+201C, `–` U+2013, `‒` U+2012, `—` U+2014, `―` U+2015, and `‘` U+2018)
- Sub-phrase delimiters: `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, `―` followed by a space.

Go's standard library `regexp` package (RE2) does not support lookahead, lookbehind, or backreferences, and its word boundary `\b` operates strictly on ASCII word characters. The Go implementation MUST hand-code equivalent string scanning, Unicode character inspection, and rune iteration logic wherever Python regular expressions depend on semantics not provided by RE2.

### Edge-Case Categories
The Go implementation MUST match the Python reference implementation byte for byte across all input categories, specifically including:
- Empty input lines
- Input lines with the same split and join behaviour as the Python source across varied whitespace configurations
- Lines that are already entirely uppercase
- Small words positioned at the beginning or end of a line
- Small words following sub-phrase punctuation marks
- Slash-separated and hyphen-separated compound words
- Words containing straight apostrophes and curly apostrophes
- Words containing non-ASCII Unicode letters and punctuation characters

## Not Checked
- Execution speed and throughput
- Memory usage and allocation efficiency
- Error-message wording
- Code formatting style, comments, and internal documentation

## Grading
The task is evaluated using hidden automated tests. Each correct behavior earns partial credit, so you should ensure as many transformation rules and edge cases match the Python reference implementation as possible.
