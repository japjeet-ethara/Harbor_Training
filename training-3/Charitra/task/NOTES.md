# Author notes: titlecase-go

## Source and license

- Repository: https://github.com/ppannuto/python-titlecase
- Frozen commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`.
- Upstream commit date: `2024-04-05T22:03:59-07:00`.
- Source version: `2.4.1`.
- License: MIT; the actual license filename is `LICENSE.txt`.
- Copyright notice: Copyright (c) 2021 Patrick William Pannuto.
- Reference source: `environment/repo/titlecase/__init__.py`.
- Reference source SHA-256: `a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0`.
- Frozen answer runtime: CPython 3.12.14, Unicode 15.0.0, standard-library `re`. Run authoring commands with `python3.12 -S` to exclude installed site packages.

The source chooses the optional `regex` package if installed and otherwise falls back to `re`. Those branches are not semantically identical. This task explicitly fixes the `re` branch; installing `regex` while regenerating answers would change the benchmark. The source snapshot is kept in `environment/repo`, independently of the repository copy that a candidate is asked to modify.

## Rules with examples verified by execution

Every output below was obtained by executing the pinned original, not by guessing the desired capitalization. Strings use Python `repr` notation so that tabs, empty strings, and leading/trailing spaces remain visible.

### 1. Ordinary word capitalization

- Input: `'hello world'`
- Original output: `'Hello World'`

### 2. Internal small words stay lowercase

- Input: `'the lord of the rings'`
- Original output: `'The Lord of the Rings'`

### 3. Small first and last words are capitalized

- Input: `'a story of'`
- Original output: `'A Story Of'`

### 4. Subphrase after a colon

- Input: `'a story: the return'`
- Original output: `'A Story: The Return'`

### 5. Mixed uppercase tokens are preserved in a mixed-case line

- Input: `'visit NASA and iPhone now'`
- Original output: `'Visit NASA and iPhone Now'`

### 6. All-uppercase lines follow a different branch

- Input: `'NASA AND THE MOON'`
- Original output: `'Nasa and the Moon'`

### 7. Dotted initials and inline periods are preserved; a period before a space can also start a subphrase

- Input: `'U.S.A. and example.com'`
- Original output: `'U.S.A. And example.com'`

### 8. Apostrophe-prefix capitalization

- Input: `"d'artagnan l'amour o'brien"`
- Original output: `"d'Artagnan l'Amour O'Brien"`

### 9. Mc-prefix recursion

- Input: `'mcdonald mcDonald MCDONALD'`
- Original output: `'McDonald McDonald McDonald'`

### 10. Honorific branch preserves the remainder

- Input: `'mr mrs ms dr DR mR'`
- Original output: `'Mr Mrs Ms Dr DR MR'`

### 11. Single slash recurses; double slash does not trigger this branch

- Input: `'a story of and/or over/under'`
- Original output: `'A Story of and/or Over/Under'`

### 12. Hyphens recurse with different small-word boundary treatment

- Input: `'end-to-end and a-b'`
- Original output: `'End-to-End and a-B'`

### 13. All-consonant tokens longer than two letters become acronyms; y counts as a vowel for this rule

- Input: `'cnn rhythm nth st'`
- Original output: `'CNN Rhythm NTH St'`

### 14. Whitespace is retained, and leading whitespace affects the first-word rule

- Input: `'  the\tlord  of the rings  '`
- Original output: `'  the\tLord  of the Rings  '`

### 15. Unicode uppercase can expand a single character

- Input: `'ß ﬃ ﬂower ǰolt'`
- Original output: `'SS FFI FLower J̌olt'`

### 16. Greek final sigma uses contextual lowercasing

- Input: `'ΟΣ ΟΣΑ'`
- Original output: `'Ος Οσα'`

### 17. Punctuation and non-ASCII text follow the original patterns

- Input: `'中文 [the story] (a tale)'`
- Original output: `'中文 [The Story] (A Tale)'`

### 18. Empty input title remains empty

- Input: `''`
- Original output: `''`

## Fixture provenance and scope

`tests/gen.py` extracts input strings from upstream `TEST_DATA`, adds explicit edge cases, and generates additional combinations with a dedicated `random.Random(1)` instance. It never copies upstream expected strings or creates expected answers by hand. It runs the pinned original on every input to freeze all expected bytes.

Each of the four text files contains exactly 2,000 LF-terminated records. Each input set is internally unique, and the public and hidden input sets are disjoint. Inputs include an empty title, preserved spacing, ASCII and Unicode punctuation, control characters other than CR/LF, mixed/all-uppercase contexts, apostrophes, recursive slash/hyphen combinations, Unicode expansions, Greek sigma, Turkish casing, combining marks, non-Latin scripts, and lines over 80 KiB in both sets. The files contain Unicode line-separator characters as title data; do not parse them with Python `str.splitlines()`, which splits more than LF.

`tests/data/manifest.json` records source provenance, reference runtime, byte counts, record counts, longest records, and SHA-256 digests. `scripts/check_fixtures.py` verifies those hashes, rechecks every answer against the original, and compares two fresh generations byte for byte. This is an authoring check, not a Harbor trial.

## Difficult behavior and limitations

The difficult parts are branch ordering and recursion, small-word treatment at boundaries, exact whitespace preservation, Python-style Unicode character classification, multi-character uppercase expansions, and context-sensitive lowercase sigma. Familiar titlecasing conventions are not a substitute for the pinned source. For example, the reference converts an all-uppercase NASA line differently from NASA inside a mixed-case sentence, and leading whitespace can prevent the first small word from being promoted.

The course handout warns about lookaround and backreferences in Python regular expressions in general. The selected revision's main compiled titlecase patterns do not themselves use lookaround or backreferences. Porting is still nontrivial because Python and Go character classes and case-conversion behavior differ.

A perfect score on this finite corpus does not prove equality on every possible Unicode string. Additional deterministic property-based comparisons and targeted regressions can strengthen confidence without changing the required behavior.

## Rubric and negative control

The course weights are build = 1, no_python = 1, and behavior = 4. The dependency restriction is included in the build gate so the written rule is checked. An unchanged Python repository scores zero because it does not build as Go. Deleting Python without a successful Go build also scores zero.

The visible-answer replay negative control must keep the original Python files. With build = 1, no_python = 0, and zero matching hidden answers, its score is 1/6, approximately 0.1667. If that cheat also removed Python, its base score would be 2/6, approximately 0.3333, making the handout's requested score below 0.2 impossible even with completely wrong behavior. The frozen visible-answer sequence happens to match 2 of 2,000 hidden output rows in the same positions. Therefore a replay program that retains Python and otherwise runs correctly has an expected raw-weighted score of `(1 + 4 * 0.001) / 6 = 0.16733333333333333`. This is a calculation from frozen data, not a claim that a Harbor run has completed. A low replay score establishes that this particular shortcut fails; it does not establish that every possible attack on the grader is prevented.

## Submission reflection

Hardest rules to reproduce: exact Unicode casing/classification and the order of small-word, punctuation, and recursive slash/hyphen handling. Authoring evidence must distinguish observed implementation mismatches from anticipated difficulty; consult the recorded validation results for actual failures.

Further fair hardening: add deterministically generated unseen Unicode/recursion cases and vary batch order while keeping the documented reference behavior and line protocol unchanged. Re-run the real oracle and nop after any benchmark change.
