# python-titlecase notes

- Repo URL: https://github.com/ppannuto/python-titlecase
- SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Licence: MIT License (MIT)

1. [x] Preserve a callback override before normal casing.
   - Input: `api`
   - Output: `API`
   - Example: `titlecase("api", callback=lambda word, **kwargs: "API" if word.upper() == "API" else None)`

2. [x] Keep all-caps acronyms and initialisms intact.
   - Input: `NASA`
   - Output: `NASA`
   - Example: `titlecase("NASA")`

3. [x] Handle apostrophe-leading forms with a special capitalisation rule.
   - Input: `o'clock`
   - Output: `O'Clock`
   - Example: `titlecase("o'clock")`

4. [x] Capitalise names beginning with `Mc` or `MC`.
   - Input: `mcDonald`
   - Output: `McDonald`
   - Example: `titlecase("mcDonald")`

5. [x] Capitalise honorifics such as `Mr`, `Mrs`, `Ms`, and `Dr`.
   - Input: `dr jekyll`
   - Output: `Dr Jekyll`
   - Example: `titlecase("dr jekyll")`

6. [x] Preserve mixed-case or dotted words that are already correctly formatted.
   - Input: `iPhone`
   - Output: `iPhone`
   - Example: `titlecase("iPhone")`

7. [x] Lower-case small words such as `a`, `an`, `and`, `of`, `the`, and `on` unless they are first or last.
   - Input: `a tale of two cities`
   - Output: `A Tale of Two Cities`
   - Example: `titlecase("a tale of two cities")`

8. [x] Recursively title-case slash-separated words.
   - Input: `foo/bar`
   - Output: `Foo/Bar`
   - Example: `titlecase("foo/bar")`

9. [x] Recursively title-case hyphenated words.
   - Input: `state-of-the-art`
   - Output: `State-of-the-Art`
   - Example: `titlecase("state-of-the-art")`

10. [x] Upper-case consonant-only acronyms longer than two letters.
    - Input: `brr`
    - Output: `BRR`
    - Example: `titlecase("brr")`

11. [x] Apply normal title-casing to ordinary words.
    - Input: `hello world`
    - Output: `Hello World`
    - Example: `titlecase("hello world")`
