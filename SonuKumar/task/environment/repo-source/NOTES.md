# titlecase Notes

## 1. Licence

The project uses the **MIT License (MIT)**, stated in `LICENSE.txt`.

## 2. Rules applied by `titlecase`

1. **Split input into lines.** By default, runs of carriage returns/newlines are treated as one separator. With `preserve_blank_lines=True`, each newline is preserved as a line boundary, including blank lines.
   - Example: `titlecase("one\n\ntwo")` -> `"One\nTwo"`
   - With preservation: `titlecase("one\n\ntwo", preserve_blank_lines=True)` -> `"One\n\nTwo"`

2. **Preserve the callback's result.** When `callback` returns a non-empty replacement for a word, that replacement is used unchanged and is excluded from later first/last-small-word adjustments.
   - Example: a callback returning `"NASA"` for `"nasa"`: `titlecase("nasa", callback=callback)` -> `"NASA"`

3. **Preserve all-capital initialisms on all-uppercase lines.** A word made from one-letter or two-letter dotted uppercase initials remains unchanged when the whole line is uppercase.
   - Example: `titlecase("MEET U.S. AT 5")` -> `"Meet U.S. at 5"`

4. **Special-case words beginning with d', l', or o'.** The letter after the apostrophe is capitalized; the first letter is lowercased for a consonant start and capitalized for a vowel start.
   - Example: `titlecase("d'art l'amour o'neill")` -> `"d'Art L'Amour O'Neill"`

5. **Preserve and titlecase Mc names.** A word beginning with `Mc` or `MC` keeps that prefix form and titlecases the remainder recursively.
   - Example: `titlecase("mcdonald")` -> `"McDonald"`

6. **Preserve the conventional capitalization of Mr, Mrs, Ms, and Dr.** These abbreviations are changed only so their first letter is uppercase.
   - Example: `titlecase("mr mRS ms dr")` -> `"Mr Mrs Ms Dr"`

7. **Preserve words with inline periods.** Words containing a letter-period-letter pattern are left unchanged.
   - Example: `titlecase("use e.g. values")` -> `"Use e.g. Values"`

8. **Preserve mixed-case words.** A word with uppercase letters elsewhere, unless it is on an all-uppercase line, is left unchanged.
   - Example: `titlecase("visit iPhone users")` -> `"Visit iPhone Users"`

9. **Lowercase configured small words.** Words in the small-word list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `via`, and `vs`, including optional periods where defined) are lowercased.
   - Example: `titlecase("WAR AND PEACE")` -> `"War and Peace"`

10. **Titlecase slash-separated parts independently.** A single slash divides a word into recursively titlecased parts; double slashes are not split by this rule.
    - Example: `titlecase("input/output")` -> `"Input/Output"`

11. **Titlecase hyphen-separated parts independently.** Each part of a hyphenated word is recursively titlecased.
    - Example: `titlecase("state-of-the-art")` -> `"State-of-the-Art"`

12. **Lowercase ordinary words from an all-uppercase line before processing.** This allows normal title casing while preserving special uppercase cases handled earlier.
    - Example: `titlecase("THIS IS A TEST")` -> `"This Is a Test"`

13. **Treat words made only of more than two consonants as acronyms.** Such words are uppercased rather than merely having their first letter capitalized.
    - Example: `titlecase("usa bcd")` -> `"Usa BCD"`

14. **Capitalize the first letter of ordinary words while preserving leading punctuation.** The first letter found after any leading punctuation is uppercased.
    - Example: `titlecase("(hello) [world]")` -> `"(Hello) [World]"`

15. **Capitalize small words at the beginning and end of a phrase by default.** This behavior can be disabled with `small_first_last=False` and is disabled during recursive processing of slash and hyphen parts.
    - Example: `titlecase("a tale of two cities")` -> `"A Tale of Two Cities"`

16. **Capitalize small words after subphrase punctuation.** A small word following `:`, `.`, `;`, `?`, `!`, or `-` and a space is capitalized.
    - Example: `titlecase("rules: and exceptions")` -> `"Rules: And Exceptions"`

17. **Preserve original whitespace by default.** Separators matched between words are retained, including tabs and repeated spaces. With `normalise_space_characters=True`, word separators are replaced by single regular spaces.
    - Example: `titlecase("hello\t  world")` -> `"Hello\t  World"`
    - With normalization: `titlecase("hello\t  world", normalise_space_characters=True)` -> `"Hello World"`

18. **Join processed lines with newline characters.** Each processed line is returned in its original line order.
    - Example: `titlecase("first\nsecond")` -> `"First\nSecond"`
