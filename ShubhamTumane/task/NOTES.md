# python-titlecase Reference Notes

- **Repository URL:** https://github.com/ppannuto/python-titlecase
- **Commit SHA:** 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- **Licence:** The MIT License (MIT)

## Titlecase Rules

1. **Standard Word Capitalization:** Capitalizes the first letter of normal words, skipping leading punctuation characters (`!"#$%&'()*+,\-./:;?@[\\\]_`{|}~` and curly quotes/dashes).
   - Input: `the lord of the rings`
   - Output: `The Lord of the Rings`

2. **Small Words Lowercased:** Words matching `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?` (case-insensitive) are converted to lowercase when they appear in the middle of a title.
   - Input: `beauty and the beast`
   - Output: `Beauty and the Beast`

3. **First and Last Small Words Capitalized:** When `small_first_last=True` (default), small words at the very beginning or very end of a title (even next to punctuation) are capitalized.
   - Input: `a tale to tell of`
   - Output: `A Tale to Tell Of`

4. **Subphrases After Punctuation:** A small word immediately following `:`, `.`, `;`, `?`, `!`, or dash characters (`-`, `–`, `‒`, `—`, `―`) plus a space is capitalized.
   - Input: `star wars: a new hope`
   - Output: `Star Wars: A New Hope`

5. **All-Caps Lines Normalized & Initials Preserved:** If the entire input line is uppercase, normal words are lowercased before titlecasing, EXCEPT uppercase initials like `A.B.` or `U.S.A.` which remain uppercase.
   - Input: `U.S.A. TODAY AND TOMORROW`
   - Output: `U.S.A. Today and Tomorrow`

6. **Inline Periods (URLs, Domains, File Extensions) Preserved:** Words containing a period between letters (`[\w][.][\w]`) are left completely unchanged.
   - Input: `visit example.com for details`
   - Output: `Visit example.com for Details`

7. **Mixed-Case / CamelCase Words Preserved:** When the line is not all-caps, words that already have uppercase letters after the first letter (e.g., `iPhone`, `eBay`, `macOS`) are left unchanged.
   - Input: `new iPhone and eBay deals`
   - Output: `New iPhone and eBay Deals`

8. **Mac and Mc Prefixes:** Words starting with `Mc`, `mc`, or `MC` followed by 2+ characters capitalize both the `Mc` prefix and recursively titlecase the remainder.
   - Input: `ronald mcdonald and mcintosh`
   - Output: `Ronald McDonald and McIntosh`

9. **Titles (`Mr`, `Mrs`, `Ms`, `Dr`):** Honorific prefixes matching `mr`, `mrs`, `ms`, or `dr` (case-insensitive, without period) have their first letter capitalized.
   - Input: `dr smith and mrs jones`
   - Output: `Dr Smith and Mrs Jones`

10. **Apostrophe Prefixes (`d'`, `o'`, `l'`):** Words starting with `d'`, `o'`, or `l'` followed by letters (and optional `'s`) capitalize the letter after the apostrophe; vowel prefix `o'` is capitalized while consonant prefixes `d'` and `l'` stay lowercase.
    - Input: `l'enfant and o'connor`
    - Output: `l'Enfant and O'Connor`

11. **Hyphenated and Slashed Words:** Words containing `-` or `/` (excluding `//` URLs) are split on the delimiter, each segment is recursively titlecased with `small_first_last=False`, and rejoined.
    - Input: `state-of-the-art and yes/no`
    - Output: `State-of-the-Art and Yes/No`

12. **All-Consonant Acronyms:** Words longer than 2 characters consisting solely of consonants (excluding `a, e, i, o, u, y`) are converted to all uppercase.
    - Input: `welcome to npr and bbc`
    - Output: `Welcome to NPR and BBC`
