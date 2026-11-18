# Reference notes

Author: Komal. AI assistance permitted and used.

Repository: https://github.com/ppannuto/python-titlecase

Pinned commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Commit date: `2024-04-05T22:03:59-07:00`.

License: MIT. Copyright (c) 2021 Patrick William Pannuto. Original Perl version by John Gruber; Python version by Stuart Colville. Full license and upstream AUTHORS are retained. The exact source blob SHA-256 is `a3d0b99857c7672b9a13ec9df54aa187082be7d39b202dc0511e67e6f7873ef0`; `evidence/upstream-identity.json` compares all four snapshot files to Git blobs, including LF bytes.

Reference runtime: CPython 3.12.8 / Unicode 15.0.0. Optional `regex` is **not installed**. The source consequently selects standard-library `re` patterns. Different runtimes or installing `regex` can change behaviour and are outside this pinned task.

## Rules in execution order

1. Split one or more CR/LF characters and join processed lines with LF. Defaults do not preserve blank-line runs.
2. Compute all-caps as `line.upper() == line`, including lines with no cased letters.
3. Split on every captured Unicode whitespace character, preserving separators and empty words.
4. Preserve matching uppercase dotted initials only on all-cap lines.
5. Apply the apostrophe-name rule before other word rules. Lower d/l, upper o, and upper the third scalar; preserve the remainder as supplied.
6. Recognize Mc prefixes, capitalize the prefix, and recursively titlecase the suffix with first/last adjustment enabled. The suffix requires at least two scalars and starts with a word character.
7. Recognize honorifics case insensitively; uppercase only their first scalar and retain the rest.
8. Preserve word-dot-word terms, or internal ASCII capitals on lines that are not all caps.
9. Lowercase exact small words using ordered alternatives.
10. Recurse through slash-separated components when a slash occurs without a double slash, disabling first/last adjustment inside components.
11. Recurse through hyphen components, also disabling first/last adjustment.
12. Lowercase ordinary remaining words on all-cap lines.
13. Uppercase words longer than two scalars that match the ASCII consonant class case insensitively; y is excluded.
14. Otherwise uppercase the first matched punctuation-plus-word prefix. In fallback `re`, the first word character can be a digit, underscore, or non-letter word scalar.
15. Adjust small words at the first and last **word slots**, rather than the first/last nonempty word. Leading/trailing whitespace therefore matters.
16. Restore the exact captured whitespace, then capitalize small-word prefixes after a subphrase delimiter and one literal ASCII space. There is no trailing word boundary here.

Callbacks, custom small-word lists, immutable callback strings, CLI wordlist files, and non-default options are outside this task's graded default function. The pinned source contains no lookaround or backreferences in these actual default patterns, despite the assignment's general regex warning.

## Checked examples

Every output below was produced and rechecked by execution of the pinned original. JSON string notation makes whitespace and combining characters unambiguous. `tools/write_notes.py` regenerates this document and asserts every stored example before writing.

| Input (JSON string) | Original output (JSON string) |
| --- | --- |
| `"the library of the town"` | `"The Library of the Town"` |
| `"THE LIBRARY OF THE TOWN"` | `"The Library of the Town"` |
| `"the BBC and the RSPB"` | `"The BBC and the RSPB"` |
| `"A.B.C AND THE FINAL"` | `"A.B.C and the Final"` |
| `"d'arcy and o'neill"` | `"d'Arcy and O'Neill"` |
| `"O'NEILL AND L'ART'S"` | `"O'NEILL and l'ART'S"` |
| `"MCLEOD and mcdonald"` | `"McLeod and McDonald"` |
| `"McA and Mcab"` | `"McA and McAb"` |
| `"mr mRS ms DR at the hall"` | `"Mr MRS Ms DR at the Hall"` |
| `"iPhone and eBay"` | `"iPhone and eBay"` |
| `"a.b AND THE HALL"` | `"A.b AND THE HALL"` |
| `"bcd and rhythm and st"` | `"BCD and Rhythm and St"` |
| `"the arts/crafts and mother-in-law"` | `"The Arts/Crafts and Mother-in-Law"` |
| `"the a/b-c/d-e final"` | `"The a/B-C/D-E Final"` |
| `"https://civic.example/a-b"` | `"https://civic.example/a-b"` |
| `"the hall: andante via viaduct"` | `"The Hall: Andante via Viaduct"` |
| `"the hall: vs. the return"` | `"The Hall: Vs. The Return"` |
| `"the hall - an event"` | `"The Hall - An Event"` |
| `"\u00dfeta and \ufb03lm"` | `"SSeta and FFIlm"` |
| `"\u01f3UNGLE"` | `"\u01f1UNGLE"` |
| `"\u039f\u03a3 AND A\u03a3\u0301"` | `"\u039f\u03c2 and A\u03c2\u0301"` |
| `"\u0345\u03a3 and A\u0345\u03a3"` | `"\u0345\u03a3 and A\u0345\u03a3"` |
| `"\u0130STANBUL and \u017f\u017f\u017f"` | `"\u0130STANBUL and SSS"` |
| `"\u0301elm e\u0301va"` | `"\u0301elm E\u0301va"` |
| `"\u2160.test and \u216b"` | `"\u2160.test and \u216b"` |
| `"\u201cthe hall\u201d"` | `"\u201cThe Hall\u201d"` |
| `"the!!"` | `"The!!"` |
| `"the_"` | `"The_"` |
| `"a\u0345 and and\u200c"` | `"A\u0345 and And\u200c"` |
| `"\tthe hall\t"` | `"\tthe Hall\t"` |
| `"the\u00a0hall\u2028and\u2029the\u001cteam"` | `"The\u00a0Hall\u2028and\u2029the\u001cTeam"` |
| `""` | `""` |
| `" "` | `" "` |
| `"a\n\nb\r\nc\r"` | `"A\nB\nC\n"` |
| `"\n\n"` | `"\n"` |
| `"THE\n\nthe"` | `"The\nThe"` |

## Development observations

No formatter mismatch was observed in the recorded frozen-corpus or 110,000-case differential runs. The source examples expose the main compatibility traps: partial small-word matches after punctuation; apostrophe suffixes that retain their input casing; Mc suffix recursion; first/last adjustment changing an otherwise preserved dotted term; and Unicode expansions with original-string sigma context.

The recorded failures were environment/verifier issues: the host Windows Go installation could not find its link tool; an initial Harbor invocation lacked the uv tools PATH; a CLI flag applied only to hosted launches; RewardKit discovery imported a generator with a bundle-only path assumption; and the initial verifier file-size bound prevented standard-library compilation. The shipped container profile fixes the relevant packaging issues. Failed evidence is retained separately and is not reported as passing.

To make future corpora harder, add deliberately deeper compound recursion and more contextual-casing neighbours selected from every Unicode property range endpoint, while continuing to execute the original for every expected answer. No unvalidated metamorphic invariant is proposed.
