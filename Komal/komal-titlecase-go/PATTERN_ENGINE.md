# Small pattern virtual machine

The engine implements the restricted operations required by the pinned source. It does not parse regular-expression strings. Pattern definitions in `solution/internal/format/patterns.go` are trees of character classes, sequencing, ordered alternatives, repetitions, captures, and assertions. They are compiled once into `consume`, `split`, `jump`, `save`, `assertion`, and `accept` instructions.

The generic interpreter in `internal/pattern` consumes Unicode scalar positions. A `split` tries its first destination and backtracks to its second only on failure. Greedy repetition places its consuming branch first; lazy repetition places its continuation first. This preserves Python's first-success alternative semantics, rather than longest-alternative semantics. Each branch receives capture positions by value, so failed branches cannot leak captures. Five capture groups are sufficient for the source's honorific pattern. Group zero records the entire match.

`Match` starts at position zero; `Search` tries positions from left to right. `$` accepts the true end or the position immediately preceding one final LF. The strict end assertion used by the consonant pattern accepts only the true end. Word boundaries use changes in the generated Python `re` word property, including the distinction between letters and combining marks. Dot excludes LF. Substitution searches the original input from left to right and resumes at the previous match's end. Replacement text is never rematched. Split can return delimiter captures, reproducing the whitespace split used by the reference.

This is a deliberately restricted compatibility engine. It has no pattern-string parser, arbitrary flags, backreferences, lookaround, Unicode property language, or empty-match substitution semantics. None is needed by this pinned default implementation's fallback `re` patterns. Unbounded repetition of a nullable pattern is rejected at compilation; replacement and splitting reject empty matches. All installed production patterns satisfy these contracts. The engine is not intended as a public regex library or for untrusted arbitrary patterns.

## Pattern data

| Data name | Original operation |
| --- | --- |
| lines | `[\r\n]+` split |
| spaces | captured `\s` split |
| small | anchored ordered small-word alternatives, case insensitive |
| first | punctuation capture, small-word capture, word boundary |
| last | word boundary, small word, optional one punctuation character, end |
| subphrase | delimiter and literal space, then ordered small alternatives without a trailing boundary |
| mc | ordered `[Mm]c` or `MC`, then word character and one or more non-LF characters |
| honorific | original nested captures and ordered alternatives |
| inline | word, dot, word; searched anywhere |
| internal | lazy punctuation, greedy ASCII letters, lazy ASCII capitals |
| cap | start, lazy punctuation, word capture |
| apostrophe | case insensitive d/o/l, apostrophe, word repetition, optional two-character suffix |
| initials | repeated ordered upper-dot or upper-dot-upper alternatives |
| consonants | case insensitive ASCII consonant class between strict anchors |

The apparently odd alternative order and missing boundary in `SUBPHRASE` are preserved. For example, its `v` alternative may win before `via` or `vs`; a subsequent substitution may capitalize the small word after a period. These are observable details, not style decisions.

## Formatting order

The formatter first splits CR/LF runs and determines `line.upper() == line`. It splits each line on captured single whitespace characters, preserving empty words and exact separators. For each word it applies: all-cap initials preservation; apostrophe names; Mc recursion; honorifics; inline periods or eligible internal capitals; small-word lowering; single-slash compounds; hyphen compounds; all-cap lowering; consonant acronyms longer than two scalars; first-word-character capitalization. Then it adjusts first and last small words, rejoins original separators, applies subphrase substitutions, and rejoins lines with LF.

Compound calls use the original recursive function semantics. The implementation has no explicit formatting stack. Mc suffixes enable first/last adjustment; slash and hyphen components disable it. The pattern VM performs recognition only; every casing or text replacement lives in the formatter or Unicode compatibility package.

## Python compatibility

`tools/gen_unicode.py` enumerates all Unicode scalars in CPython 3.12.8, without the optional regex package. It generates `re` word and whitespace ranges, full single-character upper/lower/title mappings, and ASCII case-insensitive equivalence classes by executing `re` for every scalar. No Go Unicode classification, casing, folding, or regex boundary implementation is used.

Final-sigma context is reconstructed from generated Cased and Case_Ignorable sets. Cased is measured using Python's single-character upper/lower/title predicates. Case_Ignorable is identified by two direct Python lowercasing probes around sigma: `AΣ+c+A` must use medial sigma while `AΣ+c` must use final sigma. The second probe distinguishes ordinary cased characters from ignored ones. Lowercase context scans the original whole string; capitalization titlecases its first scalar and lowercases subsequent scalars with that same original context. Full mappings can expand one scalar into several. No normalization is performed.

Direct engine fixtures were generated by `tools/gen_patterns.py` and checked before end-to-end integration testing: 61,416 Python match/search results, including ambiguous patterns, match positions, and every capture. Generic tests additionally cover greedy backtracking, lazy choice, capture rollback, strict anchors, non-overlapping replacement, and rejection of nullable loops. This verification is evidence of compatibility on those cases, not a formal proof for all strings.
