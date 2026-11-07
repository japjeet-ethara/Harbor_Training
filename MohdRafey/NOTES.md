# Notes on `titlecase` (version 2.4.1)

# Project Information
Project: python-titlecase
Repository: https://github.com/ppannuto/python-titlecase
Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167 2024-04-05T22:03:59-07:00

Sources: `titlecase/__init__.py` and `LICENSE.txt`.

## 1. Licence

**The MIT License (MIT)**, copyright (c) 2021 Patrick William Pannuto. The header of `titlecase/__init__.py` also points to the MIT licence.

## 2 and 3. Rules and examples

The rules are listed in the order the code applies them. Rules 4 to 15 are checked word by word, and the first one that matches decides the word, except rule 13, which changes the word and carries on. Line numbers refer to `titlecase/__init__.py`.

In the examples, `\n` is a newline and `\t` is a tab.

### Whole-line rules, applied before looking at words

| # | Rule | Input | Output |
|---|------|-------|--------|
| 1 | Split the text into lines and process each one separately. Blank lines are dropped, and the output is joined with `\n` (lines 100-103, 212). | `first\n\n\nsecond` | `First\nSecond` |
| 2 | With `preserve_blank_lines=True`, blank lines are kept (line 101). | `first\n\n\nsecond` | `First\n\n\nSecond` |
| 3 | A line with no lowercase letters counts as all caps, so its words are lowercased before being recased. This is decided per line, not per text (lines 106, 168-169). | `THE LORD OF THE RINGS` | `The Lord of the Rings` |

### Word rules, in order

| # | Rule | Input | Output |
|---|------|-------|--------|
| 4 | **Callback.** If a `callback` returns a value for a word, that value is used as is. Later steps, including rules 16 and 17, leave it alone (lines 112-118, 186, 192). The example callback returns `TCP` for "tcp" and `udp` for "udp". | `udp and tcp` | `udp and TCP` |
| 5 | **Initials on all-caps lines.** A word such as `V.` or `J.R.R.` is kept unchanged on an all-caps line (lines 120-123). | `JOHN V. SMITH` | `John V. Smith` |
| 6 | **Apostrophe prefixes.** For words starting `d'`, `o'` or `l'`, the letter after the apostrophe is capitalised. A leading `o` is capitalised too, while `d` and `l` are lowercased (lines 125-131). | `o'reilly media` | `O'Reilly Media` |
| | | `d'artagnan rides` | `d'Artagnan Rides` |
| 7 | **Mc names.** `Mc` is capitalised and the rest of the word is title-cased separately (lines 133-137). It needs at least two letters after `Mc`, and `Mac` is not treated this way. | `mcdonald farm` | `McDonald Farm` |
| 8 | **Titles.** `Mr`, `Mrs`, `Ms` and `Dr` get a capital first letter, and the rest of the word is unchanged (lines 139-143). | `visit mr smith and dr jones` | `Visit Mr Smith and Dr Jones` |
| 9 | **Inline periods.** A word with a period between two letters is kept unchanged, which covers domains and URLs (line 145). | `visit example.com today` | `Visit example.com Today` |
| 10 | **Capitals inside a word.** On a line that is not all caps, a word with a capital after its first letter is kept unchanged (line 145). | `the iPhone and eBay story` | `The iPhone and eBay Story` |
| | | `NASA rocks` | `NASA Rocks` |
| 11 | **Small words.** These are lowercased: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs. (lines 28, 148-150). | `war and peace` | `War and Peace` |
| 12 | **Slashes and hyphens.** Each part between `/` or `-` is title-cased separately, without rules 16 and 17, so small words stay lowercase. Words containing `//` skip the slash step (lines 152-166). | `read this and/or that` | `Read This and/or That` |
| | | `mother-in-law` | `Mother-in-Law` |
| 13 | **All-caps lowering.** A word that reaches this point on an all-caps line is lowercased, then continues to rules 14 and 15 (lines 168-169). | `HELLO WORLD` | `Hello World` |
| 14 | **All-consonant acronyms.** A word of three or more letters with no a, e, i, o, u or y is fully capitalised (lines 174-180). | `the bbc and the html spec` | `The BBC and the HTML Spec` |
| | | `st john` | `St John` |
| 15 | **Default.** Any other word gets a capital on its first letter, skipping leading punctuation (line 183). | `'hello' world` | `'Hello' World` |

### Finishing rules, applied to the rebuilt line

| # | Rule | Input | Output |
|---|------|-------|--------|
| 16 | **First word.** A small word at the start of a line is capitalised, even after leading punctuation (lines 185-190). | `(the end) of it` | `(The End) of It` |
| 17 | **Last word.** A small word at the end of a line is capitalised, even with one punctuation mark after it (lines 192-195). | `what is it good for?` | `What Is It Good For?` |
| 18 | **Turning off rules 16 and 17.** With `small_first_last=False`, first and last small words stay lowercase (lines 80, 185). | `the end of` | `the End of` |
| 19 | **Spacing.** Original whitespace is kept (lines 200-203). | `a  tale\tof two` | `A  Tale\tof Two` |
| 20 | **Normalised spacing.** With `normalise_space_characters=True`, each whitespace character becomes a normal space (lines 197-198). | `a tale\tof two` | `A Tale of Two` |
| 21 | **Subphrases.** A small word is capitalised after `:`, `.`, `;`, `?`, `!` or a hyphen or dash, when followed by a space (lines 35, 205-208). | `star wars: a new hope` | `Star Wars: A New Hope` |
| | | `wait - a moment` | `Wait - A Moment` |

## Surprising behaviour

The rules above produce these results, which may not be what you would want:

| Input | Output | Why |
|-------|--------|-----|
| `O'REILLY MEDIA` | `O'REILLY Media` | Rule 6 never lowercases the rest of the word. |
| `MR SMITH AND MRS JONES` | `MR Smith and MRS Jones` | Rule 8 runs before all-caps lowering. |
| `IPHONE` | `Iphone` | Rule 10 only applies on lines that are not all caps. |
| `mcat exam` | `McAt Exam` | Rule 7 treats any word starting `mc` as a name. |
| `hmm that is odd` | `HMM That Is Odd` | Rule 14 treats any word without vowels as an acronym. |
| `this and/or` | `This and/Or` | Rule 17 matches the `or` after the slash. |
| `foo: inDesign rocks` | `Foo: InDesign Rocks` | Rule 21 sees the small word `in` at the start of `inDesign`. |
| `http://foo/bar now` | `Http://foo/bar Now` | A URL with no period between letters is not protected by rule 9. |

`set_small_word_list()` (lines 69-77) replaces the small-word list, but it also rebuilds rule 21 without the hyphen and dashes. After calling it, even with the default list extended, `wait - a moment` gives `Wait - a Moment`.

## How the examples were checked

Every example was run through the real function. This machine does not have the optional `regex` package, so the code used its fallback to Python's built-in `re`. With `regex` installed, non-ASCII letters are handled better by rules 5, 6, 9, 10 and 15. The examples here are all ASCII, but they have not been run with `regex` installed.
