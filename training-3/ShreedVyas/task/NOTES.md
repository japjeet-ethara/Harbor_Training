# python-titlecase source notes

- Repository: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`
- Commit date: `2024-04-05T22:03:59-07:00` (from `git log -1 --format='%H %cI'`)
- License: MIT (from `LICENSE.txt`, whose first line is `The MIT License (MIT)`)
- Regex runtime: `titlecase/__init__.py` tries to import optional `regex` (lines 17-21), then falls back to standard-library `re` when unavailable. This task's answer-key runtime is standard-library `re`: `python -m pip list` showed only the package headings and no `regex` package, and `importlib.util.find_spec('regex')` returned `False`.

## Rules and verified examples

Each output below was obtained by running the original `titlecase()` from this checkout.

1. The listed small words are lowercased when they occur as regular words. Source: `titlecase/__init__.py`, lines 28, 31, 150-153. Example: `the lord of the rings` -> `The Lord of the Rings`.
2. A small word at the beginning or end of a line is capitalized. Source: `titlecase/__init__.py`, lines 33-34, 185-195. Example: `a tale of two cities` -> `A Tale of Two Cities`.
3. A small word following punctuation and a space that starts a subphrase is capitalized. Source: `titlecase/__init__.py`, lines 35, 202-205. Example: `war and peace: a new beginning` -> `War and Peace: A New Beginning`.
4. An `Mc`/`MC` prefix receives special capitalization, and its remainder is recursively titlecased. Source: `titlecase/__init__.py`, lines 36, 133-136. Example: `mcdonald and mcdowell` -> `McDonald and McDowell`.
5. `Mr`, `Mrs`, `Ms`, and `Dr` retain an initial capital and lowercase remainder. Source: `titlecase/__init__.py`, lines 37, 140-143. Example: `dr smith and mr jones` -> `Dr Smith and Mr Jones`.
6. Words with an inline period or existing uppercase letters after a lowercase letter are preserved. Source: `titlecase/__init__.py`, lines 40-50, 145-148. Example: `iPhone and eBay` -> `iPhone and eBay`.
7. Words beginning with `d'`, `l'`, or `o'` apply special capitalization to the letters around the apostrophe. Source: `titlecase/__init__.py`, lines 43, 49, 124-130. Example: `o'neill and l'amour` -> `O'Neill and l'Amour`.
8. In an all-uppercase line, uppercase initials such as `J.` and `R.` are retained while other words are titlecased. Source: `titlecase/__init__.py`, lines 44, 50, 109-122. Example: `J. R. R. TOLKIEN` -> `J. R. R. Tolkien`.
9. A word with single slashes is split and each part is recursively titlecased; words containing `//` are not split by this rule. Source: `titlecase/__init__.py`, lines 155-164. Example: `rock/roll` -> `Rock/Roll`.
10. A hyphenated word is split and each part is recursively titlecased. Source: `titlecase/__init__.py`, lines 166-171. Example: `state-of-the-art` -> `State-of-the-Art`.
11. When an entire line is uppercase, words are lowercased before normal title capitalization. Source: `titlecase/__init__.py`, lines 109-110, 173-175. Example: `NASA AND FBI` -> `Nasa and Fbi`.
12. A word longer than two characters made only of consonants other than `y` is treated as an acronym and uppercased. Source: `titlecase/__init__.py`, lines 172-180. Example: `bcdf` -> `BCDF`.
13. The first letter after leading punctuation is capitalized. Source: `titlecase/__init__.py`, lines 42, 48, 182-184. Example: `...hello, WORLD` -> `...Hello, WORLD`.
14. Line breaks are processed as separate lines and preserved in the returned text. Source: `titlecase/__init__.py`, lines 101-107, 207-210. Example: `hello` followed by a newline and `world` -> `Hello` followed by a newline and `World`.
