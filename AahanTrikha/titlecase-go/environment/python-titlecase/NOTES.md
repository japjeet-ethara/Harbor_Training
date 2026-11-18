# python-titlecase reference notes

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05T22:03:59-07:00
- License: MIT License (MIT), provided in LICENSE.txt.

## Rules applied by titlecase()

1. Small words (`a`, `an`, `the`, `and`, etc.) are lowercased except when start/end overrides apply. Example: `war and peace` -> `War and Peace`.
2. Small words at the beginning and end are capitalized by default. Example: `a tale of two cities` -> `A Tale of Two Cities`.
3. Entirely uppercase lines are normalized to title case, while dotted initials remain uppercase. Example: `NASA AND THE FBI` -> `Nasa and the Fbi`.
4. Mixed-case words and words with an internal period are preserved. Example: `iPhone macOS eBay U.S.A.` -> `iPhone macOS eBay U.S.A.`.
5. Hyphenated components are titlecased recursively; small words in components follow recursive rules. Example: `state-of-the-art design` -> `State-of-the-Art Design`.
6. Slash-separated components are titlecased recursively unless an earlier mixed-case preservation rule matches the whole token; `//` skips this branch. Example: `war/and/peace` -> `War/and/Peace`.
7. Apostrophe forms beginning d/o/l capitalize the second segment; common honorifics and Mc names have special capitalization. Example: `o'neill mcDonald dr smith` -> `O'Neill McDonald Dr Smith`.
8. Punctuation is retained; punctuation does not prevent capitalization of the first letter. Example: `"the (quick) fox"` -> `"The (Quick) Fox"`.
9. The first word after a colon, period, semicolon, question mark, exclamation mark, or hyphen plus space is capitalized, even when small. Example: `notes: and then we left` -> `Notes: And Then We Left`.
10. Whitespace separators are preserved; leading whitespace creates an empty first token and therefore prevents the first-word override. Example: `  a  tale` -> `  a  Tale`.
11. Tokens made only of ASCII consonants longer than two characters become uppercase when earlier case-preservation rules do not match; `y` is excluded from the consonant set. Example: `bcdf and xzq` -> `BCDF and XZQ`.
12. Ordinals and numbers retain their digits while adjacent words receive normal title casing. Example: `chapter 2: the 3rd act` -> `Chapter 2: The 3rd Act`.

## Tricky observations used in corpus design

- Leading whitespace creates an empty first token, so a small first word stays lowercase; trailing whitespace creates an empty last token, so a small last word stays lowercase.
- A slash token such as `WAR/and/PEACE` can be preserved whole by the earlier mixed-case detector because the token contains uppercase letters but its line is not entirely uppercase.
- Entirely uppercase lines are normalized before the consonant acronym check, while internal-capital preservation happens before slash and hyphen recursion.
- Whitespace separators are preserved byte-for-byte except that the line-oriented task treats CRLF as a line boundary.
