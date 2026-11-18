import json
from reference import ROOT, SHA, SOURCE, digest, load

ref = load()
examples = json.loads((ROOT / 'titlecase-go/solution/internal/format/testdata/examples.json').read_text())
for row in examples:
    assert row['expected'] == ref.titlecase(row['input'])
text = f'''# Reference notes

Author: Komal. AI assistance permitted and used.

Repository: https://github.com/ppannuto/python-titlecase

Pinned commit: `{SHA}`. Commit date: `2024-04-05T22:03:59-07:00`.

License: MIT. Copyright (c) 2021 Patrick William Pannuto. Original Perl version by John Gruber; Python version by Stuart Colville. Full license and upstream AUTHORS are retained. The exact source blob SHA-256 is `{digest(SOURCE)}`; `evidence/upstream-identity.json` compares all four snapshot files to Git blobs, including LF bytes.

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
'''
for row in examples:
    text += '| `' + json.dumps(row['input'], ensure_ascii=True) + '` | `' + json.dumps(row['expected'], ensure_ascii=True) + '` |\n'
text += '''
## Development observations

No formatter mismatch was observed in the recorded frozen-corpus or 110,000-case differential runs. The source examples expose the main compatibility traps: partial small-word matches after punctuation; apostrophe suffixes that retain their input casing; Mc suffix recursion; first/last adjustment changing an otherwise preserved dotted term; and Unicode expansions with original-string sigma context.

The recorded failures were environment/verifier issues: the host Windows Go installation could not find its link tool; an initial Harbor invocation lacked the uv tools PATH; a CLI flag applied only to hosted launches; RewardKit discovery imported a generator with a bundle-only path assumption; and the initial verifier file-size bound prevented standard-library compilation. The shipped container profile fixes the relevant packaging issues. Failed evidence is retained separately and is not reported as passing.

To make future corpora harder, add deliberately deeper compound recursion and more contextual-casing neighbours selected from every Unicode property range endpoint, while continuing to execute the original for every expected answer. No unvalidated metamorphic invariant is proposed.
'''
(ROOT / 'NOTES.md').write_text(text, encoding='utf-8')
print(f'NOTES.md: {len(examples)} examples rechecked against original source')
