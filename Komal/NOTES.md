# Komal: source and validation notes

Source: https://github.com/ppannuto/python-titlecase

Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`

Commit date: `2024-04-05T22:03:59-07:00`. License: MIT.

Reference: CPython 3.12.14, regex 2026.11.9, `REGEX_AVAILABLE=True`.

## Rules

1. Process each record independently; split the function's text on CR/LF runs.
2. Preserve individual whitespace separators, including empty edge fields.
3. Keep uppercase dotted initials on all-caps lines.
4. Recase d/l/o apostrophe names before ordinary capitalization.
5. Recurse on Mc/mc/MC names with edge handling enabled. Mac is not special.
6. Capitalize only the first character of matched honorifics.
7. Preserve tokens containing a letter-period-letter sequence.
8. Preserve internal capitals on lines that are not entirely uppercase.
9. Lowercase the fixed small-word list.
10. Recurse on single slash compounds, excluding double slashes.
11. Recurse on hyphen compounds with edge handling disabled.
12. Lowercase remaining tokens when their whole line is uppercase.
13. Uppercase consonant-only words longer than two characters; y is a vowel.
14. Capitalize the first letter after permitted leading punctuation.
15. Apply first/last small-word rules to split fields, including empty fields.
16. Apply the case-sensitive, non-overlapping subphrase scan after reassembly.
17. Use Python casing expansions and contextual Greek final sigma.

## Examples checked against the original

- `'the lord of the rings'` → `'The Lord of the Rings'`
- `' the cat'` → `' the Cat'`
- `'the cat of '` → `'The Cat of '`
- `'x. v. a b'` → `'X. V. a B'`
- `'vs. a b: vs. a'` → `'Vs. A B: Vs. A'`
- `'MR SMITH GOES TO NASA'` → `'MR Smith Goes to Nasa'`
- `"d'artagnan"` → `"d'Artagnan"`
- `"l'grange"` → `"l'Grange"`
- `"o'reilly"` → `"O'Reilly"`
- `'mcthe'` → `'McThe'`
- `'macdonald'` → `'Macdonald'`
- `'a-b the-the'` → `'A-B the-The'`
- `'v1.2'` → `'V1.2'`
- `'iTunes and eBay'` → `'iTunes and eBay'`
- `'\u039f\u03a3 \xdf \u0130 \ufb01'` → `'\u039f\u03a3 SS \u0130 FI'`
- `'a\tthing'` → `'A\tThing'`
- `'34th 3rd 2nd'` → `'34th 3rd 2nd'`

## Development observations

The first differential check of the completed Go implementations had zero
mismatches across all three 4,000-record corpora. A separate 100,000-record audit
also agreed exactly. No claim of repeated titlecase failures is made.

Harness validation caught and corrected RewardKit filename grouping, explicit
weights for individual score exports, and executable-jail placement on hosts
whose temporary filesystem is mounted noexec. These were harness defects,
not titlecase rule failures.

## Scoring limits

The prescribed weights are unchanged: `(build + no_python + 4*behaviour)/6`.
A buildable empty program with Python removed can therefore earn 1/3; this is
a consequence of section 18's partial-credit scheme. The required replay
baseline intentionally leaves Python files and should earn 1/6.

A finite corpus does not prove equivalence for every possible string. The
extra audit and contract tests strengthen evidence without changing grading.
A fresh, independent model attempt has not been claimed.

## Komal's implementation

A word inspection step either emits a completed value or schedules child documents. Separate stack operations process documents and lines and assemble their values in order. Mc names schedule a prefix plus a child with edge handling enabled; slash and hyphen compounds schedule children with edge handling disabled. This retains the original evaluation order while replacing recursive formatter calls with an explicit work stack. Unicode/casing helpers and the verifier are shared with the earlier submissions.

## Corpus design

Sixteen editorial-title families each contribute 250 records, split evenly into 125 visible and 125 hidden records. Families cover opening and closing small words, apostrophes, nested Mc names, honorifics, brands, dotted words, initials, consonants, slash and hyphen compounds, compound interactions, subphrases, Unicode, spacing, and punctuation. Seed 1 controls all sampling. The original pinned Python function supplies every answer. Inputs and expected outputs are unique across the two splits.

## Hand-in observations

The compatibility risks are casing expansions, Unicode word boundaries, subphrase alternation order, and edge handling inside nested compounds. Differential validation found no output mismatches; no invented failure history is claimed. A separate callback/multiline task or independent Unicode holdout would make a future task harder.
