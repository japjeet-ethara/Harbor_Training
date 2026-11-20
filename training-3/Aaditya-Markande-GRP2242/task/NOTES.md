# python-titlecase notes

- Repo: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05T22:03:59-07:00
- Version: 2.4.1
- Licence: MIT (confirmed from LICENSE.txt: "The MIT License (MIT)", Copyright (c) 2021 Patrick William Pannuto)

Function: titlecase(text) in titlecase/__init__.py. Only the defaults are used
(no callback, small_first_last=True, preserve_blank_lines=False,
normalise_space_characters=False).

Small words (not capitalised in the middle of a title):
a an and as at but by en for if in of on or the to v v. via vs vs.

## Rules

1. Text is split on newlines (runs of \r or \n); each line is processed alone and the
   results are joined with \n.
   "the end\n\nof days" -> "The End\nOf Days"

2. A line is split on single whitespace characters; the original spaces are kept.
   "the   lord" -> "The   Lord"

3. A normal word gets its first letter capitalised; the other letters are NOT changed.
   "hello world" -> "Hello World"

4. Small words in the middle stay lowercase.
   "the lord of the rings" -> "The Lord of the Rings"

5. The first and the last word are capitalised even if small.
   "what is this for" -> "What Is This For"

6. If the whole line is uppercase, words are lowercased first, then titlecased.
   "THE LORD OF THE RINGS" -> "The Lord of the Rings"

7. A word made only of consonants (a-z, y is not a vowel here) and longer than 2
   letters is uppercased (acronym guess). Two-letter ones are not.
   "the nbc and cnn" -> "The NBC and CNN"
   "st louis" -> "St Louis"

8. A word with a capital letter after its first letter is kept as it is
   (not applied when the whole line is uppercase).
   "the iPhone review" -> "The iPhone Review"
   "NASA launches" -> "NASA Launches"

9. A word with a letter, a period, then a letter (web addresses) is kept as it is.
   "visit example.com today" -> "Visit example.com Today"

10. Mr, Mrs, Ms, Dr (any case) become Mr, Mrs, Ms, Dr.
    "dr smith and mrs jones" -> "Dr Smith and Mrs Jones"

11. Words starting with Mc / mc / MC followed by a letter: "Mc" + the rest titlecased.
    "mcdonald's farm" -> "McDonald's Farm"

12. Words like o'xxx, d'xxx, l'xxx: the letter after the apostrophe is capitalised;
    the first letter is capitalised only if it is a vowel, else lowercased.
    "o'brien and d'artagnan" -> "O'Brien and d'Artagnan"

13. A word containing "/" (but not "//") is split on "/", each part titlecased
    (small words stay lowercase), and joined with "/".
    "input/output devices" -> "Input/Output Devices"

14. A word containing "-" is split on "-", each part titlecased (small words
    stay lowercase), and joined with "-".
    "state-of-the-art design" -> "State-of-the-Art Design"

15. After : . ; ? ! or a dash followed by a space, a small word is capitalised.
    "star wars: a new hope" -> "Star Wars: A New Hope"

16. In an all-caps line, capital initials like J.R.R. are kept as they are.
    "J.R.R. TOLKIEN" -> "J.R.R. Tolkien"

17. "v." and "vs." are small words.
    "roe v. wade" -> "Roe v. Wade"

## Examples to double check (surprising real outputs from the original code)
All 19 examples above matched the real output. These extra cases from the generated
data are the rare ones that a port can easily get wrong:
- "mr s/he a" -> "Mr S/He A" (each part of a slashed word is capitalised, even "he")
- "nbc PhD st. O'NEIL" -> "NBC PhD St. O'NEIL" (mixed-case words are kept, "st." is not an acronym)
- "LANGUAGE HELLO GARDEN D'ARC." -> "Language Hello Garden D'arc." (in an all-caps line the apostrophe rule does not apply)
- "secret -- an o'clock" -> "Secret -- An O'Clock" (the letter after the apostrophe is capitalised)
- "macdonald v review nbc" -> "Macdonald v Review NBC" ("macdonald" is not treated like "mcdonald")
- "re-enter trailing- a/b" -> "Re-Enter Trailing- A/B" (a trailing hyphen is kept)