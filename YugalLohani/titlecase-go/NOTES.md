# python-titlecase — Notes

**Repository:** https://github.com/ppannuto/python-titlecase  
**Clone path:** `c:\HarborPractice\python-titlecase`  
**Latest commit (copy SHA and date here after running `git log -1 --format='%H %cI'`):**  
`<SHA> <date>`  ← fill in manually from terminal output

---

## Licence

**MIT License** — Copyright (c) 2021 Patrick William Pannuto.  
Full text in `LICENSE.txt`.

---

## Rules applied by `titlecase()`

The function processes text word-by-word, applying the following rules in order. Rules higher in the list take priority (once a rule fires, the word is appended and processing continues to the next word).

### Rule 1 — Callback override (immutable)
If a `callback` function is provided and returns a non-empty string for the word, that string is used as-is and marked immutable (no further rules apply to it).

- **Input:** `"at&t"` with callback that returns `"AT&T"` for `"AT&T"`  
- **Output:** `"AT&T"`

---

### Rule 2 — UC Initials (all-caps input only)
When the entire input line is ALL CAPS and a word matches the initials pattern (`A.`, `A.B`, `A.B.`, etc.), it is left exactly as-is.

- **Input:** `"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM"`  
- **Output:** `"Washington, D.C. Should Be Fixed but Might Be a Problem"`  
  *(D.C. is preserved; the rest is downcased and re-cased)*

---

### Rule 3 — Apostrophe-second words (d', l', o')
Words matching `^[dol]['']<letter>+` are handled specially:
- If the first character is NOT a vowel (e.g. `l'`): first char lowercased, apostrophe kept, third char uppercased.
- If the first character IS a vowel (e.g. `o'`): first char uppercased, apostrophe kept, third char uppercased.

- **Input:** `"l'grange l'grange l'Grange l'Grange"`  
- **Output:** `"l'Grange l'Grange l'Grange l'Grange"`

- **Input:** `"o'grange O'grange o'Grange O'Grange"`  
- **Output:** `"O'Grange O'Grange O'Grange O'Grange"`

---

### Rule 4 — Mc prefix (MAC_MC rule)
The regex `^([Mm]c|MC)(\w.+)` matches words where the prefix is exactly `Mc`, `mc`, or `MC` — **not** `Mac`, `mac`, or `MAC`. The prefix is capitalised (`Mc`) and the rest is titlecased recursively.

- **Input:** `"oblon, spivak, mcclelland, maier & neustadt"`  
- **Output:** `"Oblon, Spivak, McClelland, Maier & Neustadt"`

- **Input:** `"mac mc MAC MC machine"`  
- **Output:** `"Mac Mc MAC MC Machine"`  
  *(only `mc`/`Mc` match the MAC_MC rule → `Mc`; `mac`/`MAC`/`MAC` do NOT match — they fall through to other rules: `mac` → capFirst → `Mac`; `MAC` → all-caps path → lowercase → `mac` → capFirst → `Mac`; `MC` → UC_ELSEWHERE preserved; `machine` → normal capitalize → `Machine`)*

- **Input:** `"Mr McTavish went to MacDonalds"`  
- **Output:** `"Mr McTavish Went to MacDonalds"`  
  *(`McTavish`: prefix `Mc` matches, rest `Tavish` → titlecase → `McTavish`; `MacDonalds`: does NOT match MAC_MC, but UC_ELSEWHERE matches `MacD...` → preserved as-is)*

---

### Rule 5 — Mr / Mrs / Ms / Dr titles
Words matching `Mr`, `Mrs`, `Ms`, or `Dr` (case-insensitively, but NOT `Mss`) have their first character uppercased and are otherwise left alone.

- **Input:** `"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person"`  
- **Output:** `"Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"`  
  *(Note: `Mss` is NOT matched by this rule and falls through to consonant-acronym rule → `MSS`)*

---

### Rule 6 — Inline period / UC elsewhere (preserve mixed-case)
If a word contains a period between two letters (e.g. `example.com`, `del.icio.us`), or if the input is NOT all-caps and the word already has an uppercase letter somewhere after the first (e.g. `iTunes`, `OmniFocus`, `AT&T`), it is left exactly as-is.

- **Input:** `"this is just an example.com"`  
- **Output:** `"This Is Just an example.com"`

- **Input:** `"iTunes should be unmolested"`  
- **Output:** `"iTunes Should Be Unmolested"`

- **Input:** `"this is http://foo.com"`  
- **Output:** `"This Is http://foo.com"` *(double-slash prevents slash-split; inline period preserves it)*

---

### Rule 7 — Small words (articles, conjunctions, prepositions)
Words in the small-word list (`a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.`) are lowercased — **except** when they appear at the very first or last position of a line (see Rule 10).

- **Input:** `"the lord of the rings"`  
- **Output:** `"The Lord of the Rings"`

- **Input:** `"Small word at end is nothing to be afraid of"`  
- **Output:** `"Small Word at End Is Nothing to Be Afraid Of"` *(final "of" capitalised by Rule 10)*

---

### Rule 8 — Slash-separated phrases (single slash only)
Words containing `/` but not `//` are split on `/`, each part is titlecased independently (recursively, without small-first-last), then rejoined with `/`.

- **Input:** `"word/word"`  
- **Output:** `"Word/Word"`

- **Input:** `"a title and/or string"`  
- **Output:** `"A Title and/or String"` *("and/or" splits into "and" + "or", both small words, so both lowercase)*

---

### Rule 9 — Hyphen-separated phrases
Words containing `-` are split on `-`, each part is titlecased recursively (without small-first-last), then rejoined with `-`.

- **Input:** `"end-to-end"`  
- **Output:** `"End-to-End"` *("to" is a small word inside the hyphen group)*

- **Input:** `"a-b end-to-end two-not-three/three-by-four/five-and"`  
- **Output:** `"A-B End-to-End Two-Not-Three/Three-by-Four/Five-And"`

---

### Rule 10 — All-consonant acronyms (length > 2)
If the entire word consists only of consonants (no vowels, no `y`) and is longer than 2 characters, it is treated as an acronym and uppercased entirely.

- **Input:** `"Words with all consonants like cnn are acronyms"`  
- **Output:** `"Words With All Consonants Like CNN Are Acronyms"`

- **Input:** `"FOO BAR 5TH ST"`  
- **Output:** `"Foo Bar 5th St"` *(`St` is 2 chars — does NOT trigger this rule; `5th` has digits so no match)*

**Tricky:** `Mss` falls through to this rule and becomes `MSS`.

---

### Rule 11 — Normal capitalisation
All other words: the first letter after any leading punctuation is uppercased (the rest unchanged from lowercase).

- **Input:** `"'by the Way, small word at the start but within quotes.'"`  
- **Output:** `"'By the Way, Small Word at the Start but Within Quotes.'"`

---

### Rule 12 — Capitalise small word at start of line (`small_first_last=True`)
After all words are processed, if the first word (which may be a small word) is NOT immutable, it is capitalised.

- **Input:** `"a thing"`  
- **Output:** `"A Thing"`

---

### Rule 13 — Capitalise small word at end of line (`small_first_last=True`)
After all words are processed, if the last word is a small word, it is capitalised.

- **Input:** `"Small word at end is nothing to be afraid of"`  
- **Output:** `"Small Word at End Is Nothing to Be Afraid Of"`

---

### Rule 14 — Sub-phrase capitalisation after `: . ; ? ! -` (or em/en dash) + space
After the line is assembled, any small word that immediately follows one of `:.;?!` (or `–‒—―`) plus a space is capitalised.

- **Input:** `"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?"`  
- **Output:** `"Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"`

- **Input:** `"generalissimo francisco franco: still dead; kieren McCarthy: still a jackass"`  
- **Output:** `"Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass"`

---

### Rule 15 — ALL CAPS input is lowercased before re-casing
When the entire input line is all-uppercase, every word is first lowercased before the capitalisation rules are applied (so the normal rules then run on the lowercase form).

- **Input:** `"THIS IS ALL CAPS AND SHOULD BE ADDRESSED"`  
- **Output:** `"This Is All Caps and Should Be Addressed"`

- **Input:** `"EPISODE 7 — THE FORCE AWAKENS"`  
- **Output:** `"Episode 7 — The Force Awakens"`

---

### Rule 16 — Multi-line input (newline handling)
By default, blank lines are collapsed (multiple `\n` → single `\n`). With `preserve_blank_lines=True` they are kept. Each non-blank line is titlecased independently with its own first/last small-word rules.

- **Input:** `"this shouldn't\nget mangled"`  
- **Output:** `"This Shouldn't\nGet Mangled"`

---

## Unicode notes
- Works on Unicode characters (accented letters, curly quotes, non-breaking spaces, etc.).
- If the `regex` module is installed (not just `re`), Unicode letter categories are used for matching; otherwise ASCII fallbacks are used.
- Example: `"EL NIÑO A ARRIVÉ HIER"` → `"El Niño a Arrivé Hier"`
- Example: `"ÝÆ ÑØ"` → `"Ýæ Ñø"`

---

## Quick test commands

```bash
python -c "from titlecase import titlecase; print(titlecase('the lord of the rings'))"
# Expected: The Lord of the Rings

python -c "from titlecase import titlecase; print(titlecase('iTunes should be unmolested'))"
# Expected: iTunes Should Be Unmolested

python -c "from titlecase import titlecase; print(titlecase('end-to-end'))"
# Expected: End-to-End

python -c "from titlecase import titlecase; print(titlecase('Words with all consonants like cnn are acronyms'))"
# Expected: Words With All Consonants Like CNN Are Acronyms

python -c "from titlecase import titlecase; print(titlecase('a title and/or string'))"
# Expected: A Title and/or String

python -c "from titlecase import titlecase; print(titlecase('Small word at end is nothing to be afraid of'))"
# Expected: Small Word at End Is Nothing to Be Afraid Of
```
