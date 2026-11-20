# NOTES — python-titlecase

## Repository
- **URL:** https://github.com/ppannuto/python-titlecase
- **SHA:** 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- **Date:** 2024-04-05T22:03:59-07:00
- **Licence:** MIT

## Rules Applied by `titlecase()`

1. **Normal words are capitalized** — The first letter of each word is uppercased.
   - Input: `the lord of the rings` → Output: `The Lord of the Rings`

2. **Small words stay lowercase** — Words in the SMALL list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v.`, `via`, `vs.`) are lowercased mid-title.
   - Input: `the law of the land` → Output: `The Law of the Land`

3. **Small words are capitalized at start/end** — The first and last words are always capitalized, even if they are small words.
   - Input: `the the` → Output: `The The`
   - Input: `nothing to be afraid of` → Output: `Nothing to Be Afraid Of`

4. **Subphrase capitalization** — After punctuation followed by a space (`:.;?!-–‒—―`), the next small word is capitalized.
   - Input: `a tale: the beginning` → Output: `A Tale: The Beginning`

5. **ALL CAPS words are lowercased first** — If the entire line is uppercase, words are lowercased before titlecasing (except UC initials like `A.B.`).
   - Input: `THE LORD OF THE RINGS` → Output: `The Lord of the Rings`

6. **Mixed case (camelCase, etc.) is preserved** — Words with uppercase letters after the first character (e.g. `iPhone`, `eBay`) are left as-is.
   - Input: `the iPhone and eBay` → Output: `The iPhone and eBay`

7. **Inline periods preserved** — Words with letters on both sides of a period (e.g. `e.g.`, `U.S.A.`) are left unchanged.
   - Input: `the u.s.a. is great` → Output: `The u.s.a. Is Great`

8. **Apostrophe-second words** — Words like `d'Artagnan`, `O'Brien`, `l'Oreal` get special capitalization.
   - Input: `o'brien's day` → Output: `O'Brien's Day`

9. **Mc/Mac names** — Names starting with `Mc` or `Mac` capitalize the prefix and recursively titlecase the rest.
   - Input: `mcdonald` → Output: `McDonald`

10. **Mr/Mrs/Ms/Dr** — Honorifics are capitalized on the first letter only.
    - Input: `mr smith and mrs jones` → Output: `Mr Smith and Mrs Jones`

11. **Hyphenated words** — Each part of a hyphenated word is titlecased independently.
    - Input: `the self-aware robot` → Output: `The Self-Aware Robot`

12. **Slash-separated words** — Each part of a slash-separated word (but not `//` URLs) is titlecased.
    - Input: `work/life balance` → Output: `Work/Life Balance`

13. **All-consonants acronyms** — Words longer than 2 characters that are all consonants are uppercased (treated as acronyms).
    - Input: `the nfl draft` → Output: `The NFL Draft`

14. **URLs preserved** — Words containing `//` are not split on `/`.
    - Input: `visit https://example.com today` → Output: `Visit https://example.com Today`

15. **UC initials preserved** — Words like `A.B.` or `A.B.C.` (all uppercase letters with periods) are kept as-is.
    - Input: `A.B.C. NEWS` → Output: `A.B.C. News`
