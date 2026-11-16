# NOTES — python-titlecase reference

- Repo: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167 (committed 2024-04-05T22:03:59-07:00)
- Version: 2.4.1
- Licence: MIT (LICENSE.txt, Copyright (c) 2021 Patrick William Pannuto) — acceptable
- Reference behaviour is the optional `regex` package installed (REGEX_AVAILABLE=True, Unicode-aware patterns). Without it the code falls back to `re` with different patterns (\w instead of \p{Letter}); we pin the `regex` path. regex version used: 2026.11.9

## Rules of titlecase() and verified examples (every output below was produced by running the original code)

1. Lines are processed one at a time; whitespace between words is preserved exactly (split on each single whitespace char)
   - input:  `  leading and trailing  `
   - output: `  Leading and Trailing  `
2. Small words (a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, vs.) stay lowercase in the middle
   - input:  `a tale of two cities and the sea`
   - output: `A Tale of Two Cities and the Sea`
3. First and last word: a small word there IS capitalised (small_first_last), but only if the line has no leading/trailing space — the edge word is the empty string otherwise
   - input:  `what to do in a`
   - output: `What to Do in A`
4. SUBPHRASE: a small word right after '[:.;?!-–‒—―] ' (punctuation + exactly one space) is capitalised
   - input:  `hello world: a new beginning`
   - output: `Hello World: A New Beginning`
5. Words with an inline period (letter.letter) are left untouched
   - input:  `visit example.com or www.nasa.gov today`
   - output: `Visit example.com or www.nasa.gov Today`
6. Non-all-caps line: a word with an uppercase letter after the first letter (iPhone, NASA, eBay) is left untouched
   - input:  `my iPhone and NASA and eBay`
   - output: `My iPhone and NASA and eBay`
7. All-caps line (line.upper()==line): words are lowercased then capitalised; also true for lines with no cased letters
   - input:  `THE QUICK BROWN FOX`
   - output: `The Quick Brown Fox`
8. All-consonant words longer than 2 letters become fully uppercase (acronym guess)
   - input:  `tv sch ttt rhythm`
   - output: `Tv SCH TTT Rhythm`
9. Mr / Mrs / Ms / Dr (any case) keep the capital M/D and the rest as typed
   - input:  `dr. smith and mrs jones`
   - output: `Dr. Smith and Mrs Jones`
10. Mc/Mac prefix: 'Mc' + recursive titlecase of the rest
   - input:  `old mcdonald had a farm`
   - output: `Old McDonald Had a Farm`
11. Apostrophe-second words: d'/o'/l' + letters: 3rd char uppercased; first char lowercased unless it is a vowel (o)
   - input:  `o'neill and d'artagnan`
   - output: `O'Neill and d'Artagnan`
12. Hyphenated words: each part is titlecased separately (small_first_last=False, all_caps re-evaluated per part)
   - input:  `well-known state-of-the-art`
   - output: `Well-Known State-of-the-Art`
13. Slash words (single '/', no '//'): each part titlecased separately
   - input:  `and/or either/or`
   - output: `And/or Either/Or`
14. URLs with '//' are not split on slashes (fall through to hyphen / normal handling)
   - input:  `see http://my-site.com/a-b`
   - output: `See http://my-site.com/a-b`
15. Initials like A.B.C. are kept in all-caps lines
   - input:  `J.R.R. TOLKIEN`
   - output: `J.R.R. Tolkien`
16. Normal word: first letter after any leading punctuation is uppercased (CAPFIRST)
   - input:  `(hello) "world" 'quoted' 3dogs`
   - output: `(Hello) "World" 'Quoted' 3dogs`

## Why a Go port is hard (Python regex features Go's RE2 lacks)
- UC_ELSEWHERE / CAPFIRST use lazy quantifiers with \p{Uppercase_Letter}; behaviour depends on backtracking (letters+ must leave one uppercase letter).
- SMALL_FIRST / SMALL_LAST use \b with alternation whose order and backtracking ('v\.?', 'vs\.?') decide the matched span.
- SUBPHRASE has no word boundary and no ignore-case, and sub() consumes matches left to right (the 'v.' alternative eats a '.').
- UC_INITIALS is a nested quantified group with backtracking.
- Python str.upper()/lower()/capitalize() vs Go's unicode functions differ for special letters.

## Rare cases the port gets wrong when done naively (candidates for hidden tests)
- `x: v. a b` -> `X: V. a B`
- `a v. b` -> `A v. B`
- `to be or not to be ` -> `To Be or Not to Be `
- `the end of -` -> `The End of -`
- `(a) and (the)` -> `(A) and (The)`
- `'s tory` -> `'S Tory`
- `mc` -> `Mc`
- `MCDONALD` -> `McDonald`
- `mcdon` -> `McDon`
- `Mcd` -> `MCD`
- `d'a's` -> `d'A's`
- `L'ASS` -> `l'ASS`
- `O'NEIL AND D'ARTAGNAN` -> `O'NEIL and d'ARTAGNAN`
- `A.B C.D` -> `A.B C.D`
- `a-to` -> `A-To`
- `a.b-to` -> `A.b-To`
- `1.5 times the size` -> `1.5 Times the Size`
- `NASA-rocket` -> `NASA-rocket`
- `iPhone-x` -> `iPhone-x`
- `a/b//c` -> `A/b//c`
- `tv-sch` -> `Tv-SCH`
- `the vs. a` -> `The vs. A`
- `or: and` -> `Or: And`
- `x:  a` -> `X:  A`
- `v.` -> `V.`
- `vs.` -> `Vs.`
- `it's an A.I. world` -> `It's an A.I. World`

## Task design decisions (and why)

- Reference path pinned to the `regex` package being installed; stated in instruction.md. Without it the original silently uses different patterns.
- Input domain narrowed in instruction.md (no \r\n, no characters with special case mappings such as "ß", Latin + Cyrillic only), because Python's full Unicode case mapping differs from Go's per-rune mapping; "byte for byte for every input" would otherwise be unfair.
- `go build ./...` writes an executable named after the module. With module `titlecase` it collides with the Python package directory `titlecase/`. The verifier therefore builds with `-o <tmpdir>/` so a correct answer can never fail on this; instruction.md mentions it too.
- tools/gen.py lives outside tests/: Reward Kit imports every top-level .py in tests/ as a criteria file, so a generator there would be executed at grading time.
- Agent runs as non-root user `agent`; agent network is an empty allowlist (Harbor adds the model endpoint); verifier is a separate container whose input is the agent's /workspace/repo, declared as an artifact in task.toml.
- Base images use exact version tags, not SHA-256 digests (`harbor lint --select ALL` still reports unpinned-image; digests could not be looked up offline).

## Validation results (verifier logic run locally — see "Limits" below)

| Run | reward | build (w1) | no_python (w1) | behaviour (w4) |
|---|---|---|---|---|
| oracle (solution/solve.sh) | 1.0 | 1 | 1 | 1.0 |
| nop (nothing done) | 0.0 | 0 | 0 | 0.0 |
| cheat (cheat/solve.sh, prints visible answers, leaves .py) | 0.1667 | 1 | 0 | 0.0 |
| cheat variant (cheat/solve_with_cleanup.sh, also deletes .py) | 0.3333 | 1 | 1 | 0.0 |
| naive attempt (capitalise each word) | 0.4927 | 1 | 1 | 0.239 |

- The specified cheat scores below 0.2. The cleanup variant scores 0.333 purely from the two cheap structural checks (behaviour is exactly 0.0): build + no_python are "easy points" worth 2/6 of the reward. To push every cheat below 0.2, lower their weights or gate them on behaviour > 0.
- Port vs original Python: 0 differing lines on the visible and hidden sets, on 300,000 further generated lines, and on 600,000 character-level fuzz lines. A control run with `cat` as the "port" got 1952 of 2000 visible-style lines wrong, so the comparison does detect failures.
- Mutation test of the hidden set (single-rule breakages of the oracle, hidden lines wrong out of 2000): subphrase 311, smallLast 355, smallFirst 390, apostrophe 203, Mc/Mac 97, Mr/Dr 25, inline period 170, UC_ELSEWHERE 261, slash split 156, `//` exclusion 40, hyphen split 333, all-consonants 107 (and the len>2 boundary 85), all-caps lowercasing 292, em-dash in SUBPHRASE 30, dotted `v.` alternative 4. UC_INITIALS: 1 line — the rule is nearly redundant in the original (initials such as A.B. are already left alone by the inline-period rule).
- The first generator version missed two of these (`//` exclusion and `v.` consumption: 0 lines wrong); targeted templates were added and the data regenerated.

## Limits of this validation

- No Docker daemon was available, so `harbor run -a oracle|nop` was NOT executed. The oracle/nop/cheat numbers above come from running the real tests/test.sh (Reward Kit via uvx) against /workspace/repo copies built from environment/ with each solve script applied. Docker image builds (both Dockerfiles) are untested here; `harbor lint` passes with default rules.
- No model/agent attempt was run, so nothing here proves the task is hard — only that it is solvable (oracle 1.0), not gameable by do-nothing, and not gameable by the visible-answers cheat.
