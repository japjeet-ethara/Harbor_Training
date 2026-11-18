# Reference-driven coverage and mutation

`titlecase-go/tests/gen.py` is original for this submission. It calls `random.seed(1)`, uses 24 original phrase templates in four domains, and combines meaningful people, places, and topics. It does not use upstream test cases, previous submissions, external corpora, or the Go implementation as an answer key. `SEEDS`, `NAMES`, `PLACES`, `TOPICS`, `SPACES`, and `DIRECTED` in the generator are the complete seed inventory.

Examples of seed templates include a water-desk welcome, a recycling briefing, a library return notice, a league fixture, a garden-club event, a craft exchange, a lost-property announcement, and a parcel notice. The placeholders are meaningful announcement content. No numerical record IDs or meaningless uniqueness suffixes are inserted.

Mutations choose uppercase, lowercase, swapcase, outer punctuation, subphrase delimiters, whitespace replacements, edge whitespace, and paired rule topics. Compound seeds include `in/out-of-service`, `north/south-east/west`, and `a/b-c/d-e`. Every proposed record is passed to the untouched pinned Python function before acceptance. Duplicate inputs and duplicate outputs are rejected globally, then the 4,000 accepted records are shuffled and split in half. The four required files each have exactly 2,000 LF-delimited records. Splitting is always on byte LF, never Python `splitlines()`, because U+0085, U+2028 and other unusual whitespace are valid record content.

## Coverage matrix

Counts below are generator feature tags, which describe selected seed features before casing or punctuation mutations. They are not claims of instrumented branch execution. Checked direct examples and pattern fixtures independently verify the corresponding behaviours. Names can supply additional features beyond the topic tag.

| Original rule / interaction | Generator feature or construction | Evidence |
| --- | --- | --- |
| All-cap line detection | allcaps mutation; uppercase notices | allcaps counts; checked examples |
| Uppercase dotted initials | initials topic and J.R.R./A.B names | initials counts; pattern fixtures |
| Apostrophe second character | d'arcy, o'neill, l‘ouverture, optional suffixes | apostrophe counts; direct examples |
| Mc prefix recursion | mcdonald, Mcintyre, MCLEOD and McA limit | mc counts; direct pattern spans |
| Honorific priority | mr, mRs, MS, dr, Dr and mRS topics | honorific counts; mixed-case examples |
| Inline word-dot-word | a.b, names with initials, URL topics | inline and url counts |
| Internal ASCII capitals | iPhone/eBay names and eHealth topic | internal counts; allcaps interactions |
| Ordered small words | small topics; every seed includes connecting small words | small counts; via/vs ambiguity fixtures |
| Single slash and double slash exception | arts/crafts, in/out-of-service, https URL | slash and url counts |
| Hyphen and nested compounds | mother-in-law; nested slash-hyphen topics | hyphen and nested counts |
| Consonants and length threshold | bcd, RSPB, BBC, rhythm, st | consonants counts; checked threshold examples |
| CAPFIRST punctuation and word class | outer quotes/brackets; combining prefixes; digits | punctuation, combining, boundary counts |
| First/last small words | leading seed small words, directed cases, edge spaces | edge-space and directed counts |
| Subphrase substitutions | colon/semicolon/question/period/dash plus literal space | subphrase counts; prefix interactions |
| Missing trailing subphrase boundary | andante, viaduct, versus, visitor | prefix counts; direct patterns |
| Unicode expansions | ßeta, ﬃlm, ǳUNGLE, ǰana, ŉandi | unicode counts; checked outputs |
| Contextual lowercase | ΟΣ, AΣ plus combining mark | context counts; original full-string probes |
| Combining marks / word boundaries | leading acute, e+acute, U+0345, U+200C, U+203F, Roman numerals | combining and boundary counts |
| Exact whitespace and empty words | 14 separators, leading/trailing spaces, empty record | whitespace and edge-space counts |
| Deliberate two-rule interactions | second topic after delimiter; names, casing and compound combinations | interaction counts; 851 visible / 829 hidden |

Full measured counts, duplicate rejection totals, overlap measurements, and file hashes are frozen in `tests/data/coverage.json`. `records.json` records the feature tags for each input. Output overlap and input overlap are both zero. The original rejected 4 duplicate inputs and 6 duplicate outputs. Output-unique filtering is an explicit corpus design choice and does not alter reference answers.

## Reproduce

Run inside the validation image with the bundle mounted at `/project`:

```sh
python titlecase-go/tests/gen.py --out /tmp/regen-a
python titlecase-go/tests/gen.py --out /tmp/regen-b
diff -r /tmp/regen-a /tmp/regen-b
python tools/verify.py
```

The verification script regenerates twice, hashes all six files, compares them to the frozen files, and re-executes the original for every frozen input. It separately regenerates Unicode data. All expected answers in the four corpus files and the rule-example fixtures come only from execution of the pinned source.

## Independent stress corpus

`tools/verify.py` uses a separate generator and PRNG seed 871231. It does not call the dataset generator for stress inputs. Its grammar mixes arbitrary short character strings, rule-token sequences, randomly sampled Unicode scalars in contextual positions, and nested separators. It checks 110,000 distinct records against original Python execution, including random non-BMP characters. The complete stress corpus is regenerated in memory rather than shipped as another answer sheet. Its input and answer hashes are preserved in raw verification logs.

No metamorphic property is used to generate expected answers or replace reference execution. Idempotence, case-invariance, separator preservation after recursion, and English title style are not assumed. In particular, `a.b AND THE HALL` and `O'NEILL AND L'ART'S` demonstrate why intuitively reasonable casing assumptions can fail.
