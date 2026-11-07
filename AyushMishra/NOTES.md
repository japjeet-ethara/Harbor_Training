# Titlecase Analysis and Specification

## Repository Information
- **Repository URL**: `https://github.com/ppannuto/python-titlecase`
- **Commit SHA**: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- **License**: MIT License (MIT)

---

## License Details
The repository is distributed under the **MIT License (MIT)** (from `LICENSE.txt`):

> Copyright (c) 2021 Patrick William Pannuto
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

---

## Titlecase Function Rules

The `titlecase` function in `titlecase/__init__.py` applies the following rules in sequence when processing text:

### 1. Callback Rule
- **Description**: If a `callback` callable is provided, it is invoked for each word (`callback(word, all_caps=all_caps)`). If the callback returns a non-empty string, that replacement is used and wrapped as immutable (`ImmutableString` or `ImmutableBytes`) so subsequent titlecasing steps do not modify it.
- **Example Input**: `"tcp and udp"` with callback returning `"TCP"` for `"tcp"` and `"UDP"` for `"udp"`
- **Example Output**: `"TCP and UDP"`

### 2. All-Caps Uppercase Initials Preservation Rule
- **Description**: When the input line is in ALL CAPS (`line.upper() == line`), uppercase dot-separated initials (matching `UC_INITIALS`, such as `D.C.` or `A.B.`) are preserved as-is rather than being downcased.
- **Example Input**: `"WASHINGTON, D.C. SHOULD BE FIXED"`
- **Example Output**: `"Washington, D.C. Should Be Fixed"`

### 3. Apostrophe Contraction / Name Prefix Rule (`APOS_SECOND`)
- **Description**: For words matching `^[dol]['‘][\w]+(?:['s]{2})?$` (e.g., words starting with `d'`, `o'`, or `l'`):
  - If the initial letter is a consonant (like `d'` or `o'`), the initial letter is lowercased if not in vowels, but for `o'` it capitalizes the first letter and the letter following the apostrophe (`O'Reilly`), whereas for `l'` (as in `l'grange`) the `l` is lowercased and the letter following the apostrophe is capitalized (`l'Grange`).
- **Example Input**: `"my name is o'reilly and l'grange"`
- **Example Output**: `"My Name Is O'Reilly and l'Grange"`

### 4. Scottish / Irish Name Prefix Rule (`MAC_MC`)
- **Description**: Words starting with `mc` or `mc` (or uppercase `MC`) followed by letters are capitalized with `Mc` (or `Mac`) followed by recursively titlecasing the remaining suffix.
- **Example Input**: `"mcdonalds and mactavish"`
- **Example Output**: `"McDonalds and Mactavish"`

### 5. Honorifics / Titles Rule (`MR_MRS_MS_DR`)
- **Description**: Common honorifics matching `^((m((rs?)|s))|Dr)$` (e.g., `Mr`, `mr`, `Mrs`, `mrs`, `Ms`, `ms`, `Dr`, `dr`) are capitalized by forcing the first letter to uppercase followed by the rest of the string.
- **Example Input**: `"mr and dr smith"`
- **Example Output**: `"Mr and Dr Smith"`

### 6. Inline Period and Existing Uppercase Rule (`INLINE_PERIOD` & `UC_ELSEWHERE`)
- **Description**: Words containing inline periods (e.g. domain names like `del.icio.us` or `example.com`), or words that already contain uppercase letters elsewhere when the whole line is not in all-caps (e.g. `iTunes`, `OmniFocus`), are left untouched to preserve internal casing.
- **Example Input**: `"this is example.com with iTunes"`
- **Example Output**: `"This Is example.com With iTunes"`

### 7. Small Words Lowercasing Rule (`SMALL_WORDS`)
- **Description**: Uncapitalized small words defined in the small word list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, `vs.`) are downcased to all-lowercase.
- **Example Input**: `"War And Peace"`
- **Example Output**: `"War and Peace"`

### 8. Slash-Delimited Terms Rule
- **Description**: Words containing a single forward slash `/` (and not `//` like in URLs) are split by `/`, each part is recursively titlecased with `small_first_last=False`, and rejoined with `/`.
- **Example Input**: `"a title and/or string"`
- **Example Output**: `"A Title and/or String"`

### 9. Hyphen-Delimited Terms Rule
- **Description**: Hyphenated words containing `-` are split by `-`, each part is recursively titlecased with `small_first_last=False`, and rejoined with `-`.
- **Example Input**: `"a-b end-to-end two-not-three"`
- **Example Output**: `"A-B End-to-End Two-Not-Three"`

### 10. All-Consonant Acronyms Rule
- **Description**: Words longer than 2 characters consisting entirely of consonants are treated as acronyms and capitalized to all-uppercase.
- **Example Input**: `"words with all consonants like cnn are acronyms"`
- **Example Output**: `"Words With All Consonants Like CNN Are Acronyms"`

### 11. General First-Letter Capitalization Rule (`CAPFIRST`)
- **Description**: Normal words not matching previous special rules have their first letter (skipping leading punctuation) capitalized. If the line was originally all-caps, words are converted to lowercase before this capitalization.
- **Example Input**: `"hello world"`
- **Example Output**: `"Hello World"`

### 12. First Word Small Word Capitalization Rule (`SMALL_FIRST`)
- **Description**: If `small_first_last=True`, any small word located at the very start of the line (even if preceded by punctuation like quotes) is capitalized, overriding rule 7.
- **Example Input**: `"a simple test"`
- **Example Output**: `"A Simple Test"`

### 13. Last Word Small Word Capitalization Rule (`SMALL_LAST`)
- **Description**: If `small_first_last=True`, any small word located at the very end of the line (even if followed by punctuation) is capitalized, overriding rule 7.
- **Example Input**: `"nothing to be afraid of"`
- **Example Output**: `"Nothing to Be Afraid Of"`

### 14. Subphrase Capitalization Following Punctuation Rule (`SUBPHRASE`)
- **Description**: Small words immediately following major punctuation marks (`:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, `―`) and a space are capitalized as the start of a subphrase.
- **Example Input**: `"starting sub-phrase: a trick, perhaps?"`
- **Example Output**: `"Starting Sub-Phrase: A Trick, Perhaps?"`

