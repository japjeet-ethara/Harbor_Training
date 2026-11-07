# Source notes

- Source: https://github.com/ppannuto/python-titlecase
- Pinned commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00`
- Licence: MIT (`LICENSE.txt`)

## Observed `titlecase()` rules

1. Small words such as `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `via`, and `vs` are lowercased internally. Example: `war of the worlds` -> `War of the Worlds`.
2. A first or last small word is capitalized. Example: `the lord of the rings` -> `The Lord of the Rings`.
3. A small word after `:`, `.`, `;`, `?`, `!`, or a dash followed by a space is capitalized. Example: `an example: the return` -> `An Example: The Return`.
4. Existing mixed capitalization and inline initials are preserved. Example: `an iPhone and eBay story` -> `An iPhone and eBay Story`.
5. Dot-separated initials are preserved. Example: `a. b. and c.` -> `A. B. and C.`.
6. `Mc` and `Mac` prefixes titlecase their remainder recursively. Example: `mcdonald and macarthur` -> `McDonald and MacArthur`.
7. `Mr`, `Mrs`, `Ms`, and `Dr` keep their conventional capitalization. Example: `dr strange and mrs smith` -> `Dr Strange and Mrs Smith`.
8. Apostrophe forms capitalize their second component. Example: `o'connor and d'artagnan` -> `O'Connor and D'Artagnan`.
9. Hyphenated and slash-delimited components are titlecased recursively. Example: `state-of-the-art and input/output` -> `State-of-the-Art and Input/Output`.
10. All-consonant words longer than two characters become acronyms. Example: `the bbc and npr report` -> `The BBC and NPR Report`.
