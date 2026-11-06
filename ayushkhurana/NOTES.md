# NOTES — python-titlecase (task author notes, NOT for the agent)

Repo:     https://github.com/ppannuto/python-titlecase
SHA:      42f43e2de55bf003b286c6f8e8d8b2d26676a167
Date:     2024-04-05T22:03:59-07:00
Licence:  MIT (LICENSE.txt, "Copyright (c) 2021 Patrick William Pannuto") -> allowed
Version:  titlecase 2.4.1
Frozen:   plain Python `re` (optional `regex` library NOT installed -> REGEX_AVAILABLE = False)
Scope:    only titlecase(text) with default arguments, called once per line.
          NOT in scope: callback / wordlist (~/.titlecase.txt), set_small_word_list (its own test is
          skipped as a known bug), preserve_blank_lines, normalise_space_characters, the CLI.
Repo's own tests with plain re: 12 ran, OK, 1 skipped (TestSmallWordList, marked FIXME).

All examples below were produced by RUNNING the original code (Python 3.10.12, plain re).
Every one is real output. Check: ✅ = verified by running.

## How it works (order matters — first matching rule wins for each word)

The text is split into lines; each line is split into words on single whitespace characters.
The whitespace itself is kept exactly as it was. Each word goes down this list and stops at the
first rule that matches. After that, rules 14–16 run on the whole line.

## Rules

1. Line splitting — splits on runs of \r and \n, blank lines are dropped, lines re-joined with \n.
   'word\rword' -> 'Word\nWord'  ✅   (a \r becomes a newline!)

2. All-caps line — if the whole line has no lowercase letters, words are lowercased first,
   then capitalised.
   'THE QUICK BROWN FOX' -> 'The Quick Brown Fox'  ✅
   'ÉCOLE NORMALE' -> 'École Normale'  ✅

3. Spacing preserved exactly (multiple spaces, leading/trailing spaces, tabs).
   '  two   spaces   ' -> '  Two   Spaces   '  ✅
   'hello\tworld' -> 'Hello\tWorld'  ✅

4. Initials in an all-caps line are kept (e.g. U.S.).
   'ALL CAPS WITH CNN AND U.S. FLAGS' -> 'All Caps With CNN and U.S. Flags'  ✅

5. d' / o' / l' prefix — letter after the apostrophe is capitalised; d and l stay lowercase,
   o becomes uppercase.
   "d'artagnan and o'reilly and l'oreal" -> "d'Artagnan and O'Reilly and l'Oreal"  ✅
   "o'neil's day" -> "O'Neil's Day"  ✅

6. Mc / MC prefix — 'Mc' + the rest titlecased. 'Mac' gets NO special treatment.
   'mcdonald and macdonald' -> 'McDonald and Macdonald'  ✅
   "MCDONALD'S" -> "McDonald's"  ✅

7. Mr / Mrs / Ms / Dr — first letter capitalised (checked before the acronym rule, so 'mrs' is
   not turned into 'MRS').
   'mr smith and mrs jones meet dr who' -> 'Mr Smith and Mrs Jones Meet Dr Who'  ✅
   'ms' -> 'Ms'  ✅

8. Letter.letter inside a word -> word left untouched (domains, abbreviations).
   'learn more at example.com today' -> 'Learn More at example.com Today'  ✅
   'visit https://example.com/path now' -> 'Visit https://example.com/path Now'  ✅

9. Capital letters after the first letter (line not all-caps) -> word left untouched.
   'iPhone and eBay sales' -> 'iPhone and eBay Sales'  ✅
   'hELLO wORLD' -> 'hELLO wORLD'  ✅
   'the U.S. ECONOMY' -> 'The U.S. ECONOMY'  ✅

10. Small words lowercased: a an and as at but by en for if in of on or the to v v. via vs vs.
   'this vs. that v the other' -> 'This vs. That v the Other'  ✅
   'via ferrata' -> 'Via Ferrata'  ✅ (first word rule wins, see 14)

11. Slash words — each part titlecased separately (small words stay small). Words containing
    '//' are NOT split.
   'and/or the input/output' -> 'And/or the Input/Output'  ✅
   'http://localhost/x' -> 'Http://localhost/x'  ✅   (no '.' so rule 8 doesn't save it)

12. Hyphen words — each part titlecased separately. Only ASCII '-' splits; an em dash inside a
    word does not.
   'end-to-end two-by-four' -> 'End-to-End Two-by-Four'  ✅
   'x-ray of a—b' -> 'X-Ray of A—b'  ✅

13. All consonants, 3+ letters -> UPPERCASE (treated as an acronym). 'y' counts as a vowel.
    2 letters or fewer: not an acronym.
   'words with cnn and bbc' -> 'Words With CNN and BBC'  ✅
   'st john and nth degree' -> 'St John and NTH Degree'  ✅
   'rhythm and blues' -> 'Rhythm and Blues'  ✅

14. Default — first letter (after any leading punctuation) capitalised; the rest is NOT lowercased.
   '"hello" said the man' -> '"Hello" Said the Man'  ✅
   "rock 'n' roll" -> "Rock 'N' Roll"  ✅
   '34th street 3rd' -> '34th Street 3rd'  ✅

15. First and last word of a line are capitalised even if small (also after leading punctuation,
    and also at the end of a hyphen/slash word).
   'a tale of two cities' -> 'A Tale of Two Cities'  ✅
   'nothing to be afraid of' -> 'Nothing to Be Afraid Of'  ✅
   'the end of.' -> 'The End Of.'  ✅
   'two-not-three/five-and' -> 'Two-Not-Three/Five-And'  ✅
   "'by the way, small word at the start but within quotes.'" ->
       "'By the Way, Small Word at the Start but Within Quotes.'"  ✅

16. Sub-phrase — a small word after one of : . ; ? ! - – ‒ — ― followed by a space is capitalised.
   'the plan: a new start' -> 'The Plan: A New Start'  ✅
   'go now - a short film' -> 'Go Now - A Short Film'  ✅
   'v. the people' -> 'V. The People'  ✅   (side effect: 'v.' ends in '.', so 'the' counts as a sub-phrase start)

## Surprises (outputs a careless port — or a human — would likely get wrong) = future hard tests

- 'q&a with steve jobs' -> 'Q&a With Steve Jobs'   (lowercase input does NOT become Q&A;
  the repo's own test only uses 'Q&A' already capitalised)
- 'word\rword' -> 'Word\nWord'                     (\r is a line break: inputs must never contain \r)
- 'v. the people' -> 'V. The People'               (sub-phrase rule fires after 'v.')
- 'http://localhost/x' -> 'Http://localhost/x'
- 'x-ray of a—b' -> 'X-Ray of A—b'
- 'nth' -> 'NTH', 'rhythm' -> 'Rhythm', 'macdonald' -> 'Macdonald'
- 'café au lait in zürich' -> 'Café Au Lait in Zürich'  ('au' is not a small word)

## Wrong examples (agent mistakes)
(none yet — the examples above were run, not guessed)

## Warnings for later steps
- Step 2: keep THIS file outside python-titlecase/. The Dockerfile copies the whole repo folder into the
  container; a NOTES.md inside it would hand the agent our list of hard test cases.
- Step 4: freeze answers with ONE Python and record its version. These notes used Python 3.10.12 in Claude's
  VM; WSL has Python 3.14.4. Re-run the examples there once before freezing.

## Step 4 — frozen answer sheet
Generated by tests/gen.py (Random(1)) INSIDE the task image titlecase-go-env:
  docker run --rm -v "$PWD:/task" -w /task titlecase-go-env python3 -B tests/gen.py
Python 3.11.2 (container) | titlecase 2.4.1 | regex: False. Two runs identical. (Python 3.10.12 gave the same hashes.)
  inputs.txt            sha256 7f325b56e12d7bfa1618449ce660e8304a022a4389607bdebce29872b42e3b43
  expected.txt          sha256 e5f051f3aa2bd7c2eeb93ad45c748bf5a1ef9542c87376a92f40dfd064c43f00
  hidden_inputs.txt     sha256 96af81374316982599818bb2ef90f06c8d0e650906bf6d32bd630966ecf7cf82
  hidden_expected.txt   sha256 475671e25301156d405de6ba574bed4ef2f263d4cf17938fb5ae701bcee43741
More surprises seen in the data: '¿winter' stays lowercase ('¿' and '¡' are not in PUNCT);
'tcp/ip’' -> 'TCP/Ip’'; 'five-and' mid-line -> 'Five-and' but at line end -> 'Five-And'; 'Mcgregor' -> 'McGregor'.

## Step 5 — grading design
Hard rules are GATES: behaviour_share = 0 unless build, no_python, no_exec all pass; reward = behaviour only.
Practice range (dev/try_verifier.sh): nop 0.0 | buildonly 0.0 | echo 0.0225 | peek 0.0 | exec 0.0 — all as predicted.
Holes closed: python3 via os/exec (no_exec), reading /tests at grading time (program runs as nobody, /tests is 700),
network downloads (GOPROXY=off, verifier no-network), Reward Kit executing gen.py (criteria live in tests/checks/).

## Step 6 — oracle: what the port got wrong first (= what makes this task hard)
1st port: hidden 2000/2000, visible 2000/2000, but FUZZ (30,000 fresh lines) found 1 mismatch:
  'İf' -> Python 'i̇f' (re.IGNORECASE treats İ as i, so 'İf' is the small word 'if'); Go EqualFold does not.
  Python links exactly 4 non-ASCII chars to ASCII letters under re.I: İ ı -> i, ſ -> s, K (Kelvin) -> k.
After fix: 200,000 fuzz lines, 0 mismatches.
Build trap: after deleting the .py files, the empty folder titlecase/ collides with the binary that
  `go build ./...` writes for module 'titlecase' -> "build output already exists and is a directory".
Rules that need care in Go (no backtracking, ASCII-only \w \b \s in Go's regexp):
  - \w, \b, \s must be Unicode (no-break space IS whitespace in Python)
  - PUNCT excludes ” ’ ¿ ¡ (so '¿winter' stays lowercase); '_' is both PUNCT and \w
  - UC_ELSEWHERE is ASCII-only in plain re; UC_INITIALS only in all-caps lines
  - SMALL_FIRST/SMALL_LAST also act on 'AT&T' -> 'At&T' (first word) and 'q&a' -> 'Q&A' (last word)
  - SUBPHRASE is case-sensitive, needs a literal ' ', has no \b, and 'v.' consumes its '.'
  - Python full case mapping: 'ß'.upper() == 'SS', final sigma in lower()
  - Recursion: Mc-words and every slash/hyphen part run the WHOLE titlecase again (own all_caps)
