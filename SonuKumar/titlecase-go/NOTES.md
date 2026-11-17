# titlecase Notes

## Repository Information
- **Upstream Repository**: https://github.com/ppannuto/python-titlecase
- **Commit SHA**: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- **Commit Date**: `2024-04-05T22:03:59-07:00` (Fri Apr 5 22:03:59 2024)
- **License**: MIT License (MIT), stated in `LICENSE.txt`
- **Reference Package Version**: `titlecase 2.4.1`

---

## Rules Applied by `titlecase`

The `titlecase()` function converts input text into Title Case while intelligently preserving acronyms, small words, technical strings (URLs/domains), honorifics, and special capitalization forms. The list of small words follows the New York Times Manual of Style, plus `v` and `vs`.

The transformation follows these rules in sequence:

1. **Split input into lines**:
   By default, consecutive newline sequences (`\r\n`, `\r`, `\n`) are collapsed. With `preserve_blank_lines=True`, each newline is preserved as a distinct line boundary.
   - Example (default): `titlecase("one\n\ntwo")` -> `"One\nTwo"`
   - Example (`preserve_blank_lines=True`): `titlecase("one\n\ntwo", preserve_blank_lines=True)` -> `"One\n\nTwo"`

2. **Custom callback handling**:
   If a `callback` function is provided, it is invoked for each word token: `callback(word, all_caps=all_caps)`. If it returns a non-empty string, that replacement is marked immutable and excluded from subsequent transformations.
   - Example: with a callback returning `"NASA"` for `"nasa"`: `titlecase("nasa", callback=callback)` -> `"NASA"`

3. **All-capital initialisms on all-uppercase lines**:
   If the entire line is uppercase (`line.upper() == line`), a word composed of dotted uppercase initials matching `^(?:[A-Z]\.|[A-Z]\.[A-Z])+$` (such as `D.C.` or `U.S.`) is left unchanged.
   - Example: `titlecase("WASHINGTON, D.C. SHOULD BE FIXED")` -> `"Washington, D.C. Should Be Fixed"`
   - *Note on subphrase interaction*: For `titlecase("MEET U.S. AT 5")`, the result is `"Meet U.S. At 5"` because the period in `U.S.` followed by a space matches the subphrase boundary rule (`:.;?!\-–‒—―` + space), which capitalizes the following small word `at` to `At`.

4. **Special apostrophe prefixes and contractions (`d'`, `l'`, `o'`)**:
   Matches words conforming to `^[dol]['‘]\w+('s)?$` (case-insensitive). The character after the apostrophe is always capitalized. For the prefix before the apostrophe:
   - If it is a consonant (`d'`, `l'`), the initial letter is **lowercased**.
   - If it is a vowel (`o'`), the initial letter is **capitalized**.
   - Example: `titlecase("d'art l'amour o'neill")` -> `"d'Art l'Amour O'Neill"` (note that `l'` is lowercased to `l'Amour`, not capitalized).

5. **Mc names (`mc`, `Mc`, `MC`)**:
   Words starting with `mc`, `Mc`, or `MC` (case-insensitive `^([Mm]c|MC)(\w.+)`) are rewritten with the normalized prefix `Mc`, and the remainder of the word is recursively titlecased with `small_first_last=True`.
   - Example: `titlecase("mcdonald meets MCcarthy")` -> `"McDonald Meets McCarthy"`

6. **Honorific titles (`Mr`, `Mrs`, `Ms`, `Dr`)**:
   Words matching `^((m((rs?)|s))|Dr)$` (case-insensitive, without a period) have only their first character converted to uppercase (`word[0].upper() + word[1:]`), leaving subsequent characters untouched.
   - Example: `titlecase("mr mRS ms dr")` -> `"Mr MRS Ms Dr"` (note that `mRS` becomes `MRS`, preserving the uppercase `RS`).

7. **Preserve words with inline periods**:
   Words containing a letter-period-letter sequence (such as domain names, URLs, or file extensions matching `\w\.\w`) are preserved unchanged.
   - Example: `titlecase("visit example.com or del.icio.us")` -> `"Visit example.com or del.icio.us"`

8. **Preserve mixed-case words on non-uppercase lines**:
   When the line is not entirely uppercase, words that contain uppercase letters beyond leading punctuation/characters (such as `iPhone`, `eBay`, `iTunes`) are preserved unchanged.
   - Example: `titlecase("visit iPhone users")` -> `"Visit iPhone Users"`

9. **Lowercase configured small words**:
   Words matching the small-words pattern (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`) are lowercased when appearing internally.
   - Example: `titlecase("WAR AND PEACE")` -> `"War and Peace"`

10. **Titlecase slash-separated parts independently**:
    Words containing a single `/` (and not `//`, which preserves URLs like `http://`) are split on `/`, and each part is recursively titlecased with `small_first_last=False`.
    - Example: `titlecase("input/output and/or values")` -> `"Input/Output and/or Values"`

11. **Titlecase hyphen-separated parts independently**:
    Words containing `-` are split on hyphens, and each segment is recursively titlecased with `small_first_last=False`.
    - Example: `titlecase("state-of-the-art design")` -> `"State-of-the-Art Design"`

12. **Downcase ordinary words on all-uppercase lines**:
    On an all-uppercase line, words that do not match initialisms, apostrophes, Mc names, honorifics, inline periods, small words, slashes, or hyphens are lowercased prior to standard title-casing.
    - Example: `titlecase("THIS IS A TEST")` -> `"This Is a Test"`

13. **Consonant-only acronyms**:
    Words longer than two characters consisting solely of ASCII consonants (excluding vowels `a, e, i, o, u, y`) are converted to all-uppercase as acronyms.
    - Example: `titlecase("watch cnn and bbc")` -> `"Watch CNN and BBC"`

14. **Capitalize ordinary words with leading punctuation**:
    Ordinary words have their first letter capitalized following any leading punctuation.
    - Example: `titlecase("(hello) [world]")` -> `"(Hello) [World]"`

15. **Capitalize first and last words of the title line**:
    By default (`small_first_last=True`), a small word appearing as the first or last word token of the title line is capitalized.
    - Example: `titlecase("a tale of two cities")` -> `"A Tale of Two Cities"`
    - Example: `titlecase("the end of a")` -> `"The End of A"`
    - *Leading whitespace note*: Because tokenization splits on whitespace (`regex.split(r'(\s)', line)`), a title beginning with whitespace produces an empty first word token `tc_line[0] = ""`. Consequently, `SMALL_FIRST` does not match, and a following small word is not capitalized:
      - `titlecase(" a thing ")` -> `" a Thing "` (the `a` remains lowercase).

16. **Capitalize small words after subphrase punctuation**:
    A small word immediately following subphrase punctuation (`:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, `―`) and a space is capitalized.
    - Example: `titlecase("rules: and exceptions; but also notes")` -> `"Rules: And Exceptions; But Also Notes"`

17. **Preserve whitespace separators**:
    Original whitespace characters (spaces, tabs, repeated spaces) are retained. If `normalise_space_characters=True`, inter-word separators are collapsed to single spaces.
    - Example (default): `titlecase("hello\t  world")` -> `"Hello\t  World"`
    - Example (`normalise_space_characters=True`): `titlecase("hello\t  world", normalise_space_characters=True)` -> `"Hello World"`

18. **Line joining**:
    Processed lines are joined by `\n` in their original order.
    - Example: `titlecase("first\nsecond")` -> `"First\nSecond"`

---

## Test Data and Evaluation

- Generated by `titlecase-go/tests/gen.py` without artificial prefixes, directly testing rule boundaries (initial small words, trailing small words, all-caps lines, leading spaces, inline periods, apostrophes, honorifics, and acronyms).
- Visible test set (`tests/data/inputs.txt`, `tests/data/expected.txt`): 2000 lines.
- Hidden test set (`tests/data/hidden_inputs.txt`, `tests/data/hidden_expected.txt`): 2000 lines.
- The visible and hidden datasets are disjoint (0 overlapping lines).

### Dataset Checksums (SHA-256)
- `inputs.txt`: `671b288d4848671616c9982ffa6dbefcfd90fb2f2317a0d3e58caecb2732e36f`
- `expected.txt`: `82fe5989c7c2abb99d9605e4efe20dce1da50670094a2ba0d08f472102bb57a7`
- `hidden_inputs.txt`: `669f65c09892dcfdd0c332af9b8c9f8f4d538b701197abd5d97e412c170409b0`
- `hidden_expected.txt`: `6e3dee85fe8e604352e9b1b5ceebe31a2eab0754fe98b059b81059379f2ec691`

### Reward Calibration
Grader reward weights (`tests/reward.toml`):
- `build`: 1.0
- `no_python`: 1.0
- `behaviour`: 4.0
- Total weight: 6.0

Expected benchmark runs:
- **Oracle (`solution/solve.sh`)**: `build=1.0, no_python=1.0, behaviour=1.0` -> Reward = **1.0000**
- **Nop (no change applied)**: `build=0.0, no_python=0.0, behaviour=0.0` -> Reward = **0.0000**
- **Cheat (`cheat/solve.sh`)**: `build=1.0, no_python=0.0, behaviour=0.0` -> Reward = `1.0 / 6.0` ≈ **0.1667** (strictly below 0.20 threshold).
