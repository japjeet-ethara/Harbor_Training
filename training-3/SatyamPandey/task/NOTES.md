# NOTES — titlecase-go task

## Source repository
- URL: https://github.com/ppannuto/python-titlecase
- Commit: `42f43e2de55bf003b286c6f8e8d8b2d26676a167` (2024-04-05T22:03:59-07:00), version 2.4.1
- Licence: **MIT** (allowed: MIT / BSD / Apache)
- Reference environment for the frozen answers: Python 3.12.16 + `regex` 2026.9.29
  (the original prefers the `regex` package; without it the code falls back to `re`
  and behaves differently, so the task pins the `regex` code path in `instruction.md`).

## Rules applied by `titlecase()` (each example was run against the original)
1. **Small words stay lower-case** in the middle: `a an and as at but by en for if in of on or the to v v. via vs vs.`
   `a tale of two cities` -> `A Tale of Two Cities`
2. **Small first / last word is capitalised** (SMALL_FIRST / SMALL_LAST, also with trailing punctuation).
   `what is it for` -> `What Is It For`
3. **After `: . ; ? ! -` + one space, a small word is capitalised** (SUBPHRASE; case-sensitive, no word boundary).
   `chapter 1: the end` -> `Chapter 1: The End`, `hello. a world` -> `Hello. A World`
4. **ALL-CAPS lines are lower-cased first**, then titlecased (initials like `J.R.R.` are kept).
   `THE LORD OF THE RINGS` -> `The Lord of the Rings`, `J.R.R. TOLKIEN` -> `J.R.R. Tolkien`
5. **Words with an inline period are left alone** (URLs, `e.g.`, `node.js`).
   `visit http://example.com/foo now` -> `Visit http://example.com/foo Now`, `e.g. node.js` -> `e.g. node.js`
6. **Mixed-case words keep their case** (a capital after the first letter, in non-all-caps lines).
   `NASA launches new rocket` -> `NASA Launches New Rocket`, `iPhone and eBay` -> `iPhone and eBay`
7. **Consonant-only words longer than 2 letters become upper-case** (`y` counts as a vowel).
   `tv nyc ltd bcd` -> `Tv Nyc LTD BCD`
8. **Mc / MC prefix**: `mcdonald macdonald MCDONALD` -> `McDonald Macdonald McDonald`
9. **Apostrophe names `d'` `o'` `l'`**: `o'neil d'artagnan l'amour` -> `O'Neil d'Artagnan l'Amour`
10. **Honorifics** `mr mrs ms dr`: `dr smith and mrs jones` -> `Dr Smith and Mrs Jones`
11. **Hyphenated and slashed words** are titlecased piece by piece (small first/last off inside).
    `state-of-the-art` -> `State-of-the-Art`, `and/or either/or` -> `And/or Either/Or`
12. **Words not starting with a letter are left as they are** (`1st place` -> `1st Place`).
13. **Whitespace is preserved exactly** and the *first/last "word" can be an empty string*
    when a line starts/ends with a space: `  the cat` -> `  the Cat` (the small-word rule applies
    to the empty first word, not to `the`). A very good rare case.
14. `x v. y` -> `X v. Y`.

## Rare cases worth testing (the port has to get these right)
Look-ahead/look-behind-free re-implementations of: `UC_INITIALS` (`A.B.C` splits as `A.` + `B.C`),
`APOS_SECOND` (optional two-char tail `'s`), `UC_ELSEWHERE` (lazy punct prefix), `SMALL_FIRST`
(`\b` after an alternation that can end in `.`), `SMALL_LAST`, Unicode `\s` (NBSP, em space,
ideographic space) and `\w` (word boundary next to accented letters / digits / underscores).

## Task build log (what was actually done)
- Dockerfile pinned `golang:1.23`; repo copied to `/workspace/repo` without `.git`.
- Answers frozen by `tests/gen.py` (seed 1, deterministic, 2000 visible + 2000 hidden, from the original code).
- `cheat/solve.sh` ports nothing and prints the visible `expected.txt`; it must score below 0.2.
- Reward Kit: `build` (1) + `no_python` (1) + `behaviour` (4), weighted mean, separate verifier container.
- Validation: **oracle 1.0, nop 0.0, cheat 0.1667 (< 0.2)** — see `jobs/`.
- Bugs found and fixed while validating:
  1. `go build ./...` failed in the verifier because the module is called `titlecase` and the repo has a
     folder `titlecase/` (Go tried to write the binary onto the folder). Fix: `go build -o /dev/null ./...`.
  2. A stale `__pycache__/*.pyc` from the author's machine was in the image and failed `no_python`.
     Fix: removed it, and the check now looks at `.py` only (exactly what the instruction forbids).
  3. Reward Kit needs Python >= 3.12; the Go image has 3.11. Fix: `uv` + Python 3.12 in `tests/Dockerfile`.

## Day 5 hardening (2026-11-20) — details in `../HARDEN.md`
- Exam replaced: `tests/data/inputs.txt` + `answers.txt`, 100,000 titles from `kit/make_pool.py 100000 1`
  (trainer kit + extra word families), answers frozen twice by `kit/answers.py` WITH `regex`
  (0 dropped). `tests/gen.py` and the old 2,000 + 2,000 files were removed (old hidden set kept in
  `../measure/old-exam/` for the before/after measurement).
- Checks moved to `tests/checks/`. Only `behaviour` is scored; `build` / `no_python` have weight 0 and
  are a gate inside `behaviour`. The agent's program runs in Reward Kit's `Worker` (fresh unprivileged
  UID; `/tests`, `/logs/verifier`, `/workspace` unreadable). Score = `max(0, (share - 0.9) / 0.1)`.
- The new exam found a real bug in this oracle: 1,499 / 100,000 wrong (full Unicode case mapping:
  `ß`→`SS`, `ﬁ`→`FI`, `İ`→`i̇`). Fixed in `solution/solve.sh` (`casing.go`, `casetables.go`), plus the
  `regex` `\w` and `regex.I` folding (`ſ`, `K`, `İ`) found by a differential fuzz. Now 0 / 100,000.
- `cheat/solve.sh` (Day 1 cheat) still prints the OLD visible answers; kept for history.
- Re-verify (counter-attacks): `behaviour` also grades 5,000 fresh titles made at grading time
  (`tests/checks/fresh.py`, answers from `tests/original/` WITH pinned `regex`) and takes the min,
  so a lookup table of the public answers scores 0; `rules.py` also bans `os/exec` / `plugin` /
  `runtime/cgo` anywhere in the dependency tree (closes `net/http/cgi`).
- Counter-attack round 2: fresh titles now mutate ~half of their words (46% of fresh words are not in
  the public pool), because a word-by-word table learned from the public answers reached 88.8% on
  unmutated fresh titles; now 37.9% (probe-wordtable scores 0.0, `jobs/2026-11-20__16-45-53`).
