# titlecase() rules and license

## 1) Licence name

The licence in the project is the MIT License.

## 2) Rules applied by `titlecase()`

1. Capitalize the first letter of ordinary words and lowercase the rest of the word.
   - Example input: `hello world`
   - Example output: `Hello World`

2. Lowercase small words from the built-in list (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v.`, `via`, `vs.`) unless they are at the start or end of the title.
   - Example input: `the lord of the rings`
   - Example output: `The Lord of the Rings`

3. Capitalize a small word when it appears at the beginning or end of the title, even though it would normally stay lowercase.
   - Example input: `in the`
   - Example output: `In The`

4. Capitalize a small word after a colon, semicolon, question mark, or exclamation mark when it starts the next phrase.
   - Example input: `a: and then`
   - Example output: `A: And Then`

5. Preserve words that already contain internal capital letters (for example CamelCase or brand names) instead of title-casing them again.
   - Example input: `iPhone and eBay`
   - Example output: `iPhone and eBay`

6. Handle apostrophe forms such as `d'Artagnan`, `l'Enfant`, and `o'Neill` by capitalizing the letter after the apostrophe.
   - Example input: `d'artagnan o'neill`
   - Example output: `D'Artagnan O'Neill`

7. Handle `Mc...` and `MC...` names specially by capitalizing the `Mc`/`MC` prefix and then title-casing the rest.
   - Example input: `mcdonald and mcintosh`
   - Example output: `McDonald and McIntosh`

8. Handle title abbreviations such as `Mr`, `Mrs`, `Ms`, and `Dr` by capitalizing the first letter only.
   - Example input: `mr smith and mrs jones`
   - Example output: `Mr Smith and Mrs Jones`

9. Treat slash-separated words as separate words and title-case each side individually.
   - Example input: `rock/roll and black/white`
   - Example output: `Rock/Roll and Black/White`

10. Treat hyphenated words as separate words and title-case each segment individually.
   - Example input: `state-of-the-art`
   - Example output: `State-of-the-Art`

11. Treat long all-consonant words as acronyms and uppercase them.
   - Example input: `brrr`
   - Example output: `BRRR`

12. If the input is already all uppercase, lowercase it before applying the regular title-casing logic, unless it is a special-case initialism-like form.
   - Example input: `the war of the worlds`
   - Example output: `The War of the Worlds`

This list reflects the behavior implemented in `titlecase/__init__.py`.
