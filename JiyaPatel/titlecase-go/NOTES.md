# python-titlecase Notes

- **Repository URL:** https://github.com/ppannuto/python-titlecase
- **License:** MIT License

## Rules Applied by titlecase()
1. Whitespace splitting preserving spacing structure (`'the lord of the rings'` -> `'The Lord of the Rings'`).
2. Small words (`a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.`) stay lowercase unless first or last (`'war and peace'` -> `'War and Peace'`).
3. First and last words are always capitalized (`'the end is near'` -> `'The End Is Near'`).
4. Small words immediately after `:`, `;`, `?`, `!` are capitalized (`'star wars: a new hope'` -> `'Star Wars: A New Hope'`).
5. Words with internal uppercase letters are preserved untouched (`'iPhone and NASA'` -> `'iPhone and NASA'`).
6. URLs and email addresses (containing `://`, `@`, or domain dots) are preserved untouched (`'visit https://example.com/foo'` -> `'Visit https://example.com/foo'`).
7. Hyphenated compounds titlecase each part independently (`'state-of-the-art'` -> `'State-of-the-Art'`).
8. Slash-separated words titlecase each side (`'either/or'` -> `'Either/Or'`).
9. Apostrophes and contractions capitalize the initial letter without capitalizing after the apostrophe (`"don't stop"` -> `"Don't Stop"`).
10. Mac/Mc prefixes capitalize the following letter where applicable (`'mcdonald'` -> `'McDonald'`).
