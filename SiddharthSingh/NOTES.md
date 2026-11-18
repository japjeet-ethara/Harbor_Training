# Titlecase Analysis

## Repository Information
- **Repository URL**: `https://github.com/ppannuto/python-titlecase` (upstream) / `https://github.com/japjeet-ethara/Harbor_Training` (workspace)
- **Commit SHA**: `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (submodule/package) / `ab9fcce3a764b7e06abe5b4c74d800f68d898da5` (workspace)
- **Commit Date**: `Fri Apr 5 22:03:59 2024 -0700` (submodule/package) / `Fri Nov 6 13:04:33 2026 +0530` (workspace)

---

## 1. License Name
- **The MIT License (MIT)** (specifically, "The MIT License (MIT)" as stated in `LICENSE.txt` / MIT License).

---

## 2. Rules Applied by the `titlecase` Function

Below is the complete ordered list of rules applied by the `titlecase` function in [titlecase/__init__.py](file:///c:/Users/siddharthsingh/Harbor_Training/python-titlecase/titlecase/__init__.py):

1. **Line Splitting & Preservation**:
   Splits input text into lines based on newline characters (`\r\n`, `\r`, or `\n`), preserving empty lines if `preserve_blank_lines=True` or collapsing consecutive newlines if `preserve_blank_lines=False`.
2. **Line All-Caps Detection**:
   Checks whether the entire line is in all-caps (`line.upper() == line`), which influences acronym handling, case-preservation rules, and word downcasing.
3. **Word and Whitespace Tokenization**:
   Splits each line alternating between word tokens and whitespace tokens (`regex.split(r'(\s)', line)`).
4. **Custom Callback Handling**:
   If a `callback` function is provided, calls `callback(word, all_caps=all_caps)`. If the callback returns a replacement string, marks it as immutable so subsequent transformation rules do not alter it.
5. **Initials in All-Caps Lines**:
   If the line is in all-caps and the word matches uppercase initials separated by periods (e.g. `D.C.` or `U.S.A.`), retains the uppercase word as-is without lowercasing.
6. **Apostrophe Contractions / Prefixes (e.g., O', l', d')**:
   Matches patterns like `^[dol]['‘]\w+('s)?$`. If the prefix character before the apostrophe is a consonant (like `d'` or `l'`), the prefix is converted to lowercase and the letter after the apostrophe is capitalized (e.g. `l'Grange`). If it is a vowel (like `o'`), the prefix is capitalized and the letter after the apostrophe is capitalized (e.g. `O'Reilly`).
7. **Mac / Mc Prefix Capitalization**:
   Matches words starting with `Mc`, `mc`, or `MC` followed by letters (`^([Mm]c|MC)(\w.+)`). Capitalizes the prefix as `Mc` and recursively titlecases the remainder of the word.
8. **Honorific Titles & Abbreviations (Mr, Mrs, Ms, Dr)**:
   Matches common titles (`Mr`, `Mrs`, `Ms`, `Dr`) case-insensitively and capitalizes the first character while keeping remaining letters lowercase.
9. **Inline Period Preservation (File Extensions, Domain Names)**:
   Preserves words containing letters with an inline period (such as domain names, URLs, or filenames like `example.com` or `del.icio.us`) without altering their capitalization.
10. **Mixed / Internal Capitalization Preservation**:
    If the line is not all-caps and the word contains uppercase letters elsewhere beyond leading punctuation/letters (e.g. `iTunes` or `AT&T`), the word's existing capitalization is preserved untouched.
11. **Small Words Downcasing**:
    Matches predefined small grammatical words (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`) and forces them to lowercase when they appear inside titles.
12. **Slash-Delimited Slash Compounds**:
    If a word contains `/` (but not `//`, preserving URLs), splits on `/` and recursively calls `titlecase` on each slash-delimited token with `small_first_last=False`.
13. **Hyphenated Compounds**:
    If a word contains `-`, splits on `-` and recursively calls `titlecase` on each hyphen-delimited token with `small_first_last=False`.
14. **All-Caps Downcasing**:
    If the line was detected as all-caps (and did not match initials/special cases), converts the word to lowercase prior to titlecasing so that all-caps words are properly normalized.
15. **Consonant-Only Acronyms**:
    Checks if a word consists entirely of consonants (excluding vowels `a, e, i, o, u, y`). If it is longer than 2 characters, treats it as an acronym and converts it entirely to uppercase.
16. **First Letter Capitalization (Standard Title Casing)**:
    Capitalizes the first alphabetical letter of any standard word, taking into account any leading punctuation.
17. **First and Last Word Capitalization**:
    If `small_first_last=True`, capitalizes any small word that occurs as the very first word or very last word of a line (even inside leading/trailing punctuation or quotes), unless marked immutable.
18. **Sub-phrase Capitalization After Major Punctuation**:
    Capitalizes small words when they immediately follow punctuation indicating a sub-phrase or break (`:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, `―`) followed by a space.
19. **Whitespace Joining & Normalization**:
    Reconstructs the line by joining words and original whitespace tokens (or collapses whitespace to single spaces if `normalise_space_characters=True`).

---

## 3. Example Input and Output for Each Rule

1. **Line Splitting & Preservation**:
   - **Input**: `"first line\n\nsecond line"` (with `preserve_blank_lines=True`)
   - **Output**: `"First Line\n\nSecond Line"`
2. **Line All-Caps Detection**:
   - **Input**: `"THIS IS ALL CAPS"`
   - **Output**: `"This Is All Caps"`
3. **Word and Whitespace Tokenization**:
   - **Input**: `"word    word"`
   - **Output**: `"Word    Word"`
4. **Custom Callback Handling**:
   - **Input**: `"use ffmpeg here"` (with callback returning `"FFmpeg"` for `"ffmpeg"`)
   - **Output**: `"Use FFmpeg Here"`
5. **Initials in All-Caps Lines**:
   - **Input**: `"WASHINGTON, D.C. SHOULD BE FIXED"`
   - **Output**: `"Washington, D.C. Should Be Fixed"`
6. **Apostrophe Contractions / Prefixes (e.g., O', l', d')**:
   - **Input**: `"l'grange and o'reilly"`
   - **Output**: `"l'Grange and O'Reilly"`
7. **Mac / Mc Prefix Capitalization**:
   - **Input**: `"mcdonald went to mctavish"`
   - **Output**: `"McDonald Went to McTavish"`
8. **Honorific Titles & Abbreviations (Mr, Mrs, Ms, Dr)**:
   - **Input**: `"mr and dr smith"`
   - **Output**: `"Mr and Dr Smith"`
9. **Inline Period Preservation**:
   - **Input**: `"visit example.com or del.icio.us"`
   - **Output**: `"Visit example.com or del.icio.us"`
10. **Mixed / Internal Capitalization Preservation**:
    - **Input**: `"syncing itunes with ipod"`
    - **Output**: `"Syncing iTunes With iPod"`
11. **Small Words Downcasing**:
    - **Input**: `"The Tale Of A Fox And The Hound"`
    - **Output**: `"The Tale of a Fox and the Hound"`
12. **Slash-Delimited Slash Compounds**:
    - **Input**: `"dance with me/let’s face the music"`
    - **Output**: `"Dance With Me/Let’s Face the Music"`
13. **Hyphenated Compounds**:
    - **Input**: `"end-to-end two-not-three"`
    - **Output**: `"End-to-End Two-Not-Three"`
14. **All-Caps Downcasing**:
    - **Input**: `"THE FORCE AWAKENS"`
    - **Output**: `"The Force Awakens"`
15. **Consonant-Only Acronyms**:
    - **Input**: `"watch cnn and bbc"`
    - **Output**: `"Watch CNN and BBC"`
16. **First Letter Capitalization**:
    - **Input**: `"hello 'world'"`
    - **Output**: `"Hello 'World'"`
17. **First and Last Word Capitalization**:
    - **Input**: `"a small word at the start and of"`
    - **Output**: `"A Small Word at the Start and Of"`
18. **Sub-phrase Capitalization After Major Punctuation**:
    - **Input**: `"Starting Sub-Phrase: a trick, perhaps?"`
    - **Output**: `"Starting Sub-Phrase: A Trick, Perhaps?"`
19. **Whitespace Joining & Normalization**:
    - **Input**: `"hello   world"` (with `normalise_space_characters=True`)
    - **Output**: `"Hello World"`

---

## 4. Verification and Checked Examples

### Tested Example: `the lord of the rings`
- **Command / Function Call**: `titlecase('the lord of the rings')`
- **Rules applied**:
  1. Rule 17 (First and last word capitalization): `'the'` at the start -> `'The'`
  2. Rule 16 (Standard word capitalization): `'lord'` -> `'Lord'`, `'rings'` -> `'Rings'`
  3. Rule 11 (Small words downcasing): `'of'` and `'the'` (internal) remain lowercase.
- **Expected & Verified Output**: `"The Lord of the Rings"`
- **Does it match what the agent wrote / expected?**: **Yes**.

### 3 Selected Checked Examples from the Rule List:
1. **Rule 11 (Small words downcasing) & Rule 17 (First & last word capitalization)**:
   - Input: `"the lord of the rings"`
   - Output: `"The Lord of the Rings"`
   - Result: **Matches code logic and test suite**.
2. **Rule 15 (Consonant-only acronyms)**:
   - Input: `"Words with all consonants like cnn are acronyms"` (from `tests.py:54`)
   - Output: `"Words With All Consonants Like CNN Are Acronyms"`
   - Result: **Matches code logic and test suite**.
3. **Rule 7 (Mac/Mc prefix capitalization)**:
   - Input: `"mac mc MAC MC machine"` (from `tests.py:214`)
   - Output: `"Mac Mc MAC MC Machine"`
   - Result: **Matches code logic and test suite**.
