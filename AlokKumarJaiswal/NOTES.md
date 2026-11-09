# Source
- Repo: https://github.com/ppannuto/python-titlecase
- Commit SHA: 42f43e2de55bf003b286c6f8e8d8b2d26676a167
- Commit date: 2024-04-05T22:03:59-07:00
- Licence: MIT (file is LICENSE.txt)
- Installed version used for checks: titlecase 2.4.1.post1.dev4+g42f43e2de

# Verification log
- 18 of the agent's rule examples were re-run against the real Python code; all 18 matched. Not re-run: rule 2 (callback), the plain example of rule 17, and the non-default flag variants of rules 1 and 19.
- Agent error found: the rule list does not mention leading or trailing whitespace. Observed on the original: titlecase(' a thing ') == ' a Thing ' (rule 17 does not capitalize the 'a' after a leading space), and whitespace-only lines come back unchanged. 115 hidden lines start with a space and 125 end with one.
- URLs: rule 11's '//' exception and rule 8 keep web links unchanged. The hidden set has 350 URL/email-style lines. The mutation check has no mutant for the '//' exception on its own.

# Titlecase notes

## Licence

The MIT License (MIT)

## Rules applied by `titlecase`

The function title-cases each word, then applies the special cases below. Small words, which stay lowercase in the middle of a line, are `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`. That list follows the New York Times Manual of Style, plus `v` and `vs`.

1. The text is handled one line at a time. By default, consecutive line breaks are collapsed, so a blank line is dropped. With `preserve_blank_lines=True`, each line break is kept. Finished lines are joined with a newline.
   - Input: `Line number one\n\nand Line three\n`
   - Output (default): `Line Number One\nAnd Line Three\n`
   - Output (`preserve_blank_lines=True`): `Line Number One\n\nAnd Line Three\n`

2. If a callback returns text for a word, that text is used and later rules leave it alone. A callback that returns nothing lets the normal rules run.
   - Input: `a simple tcp and udp wrapper`, with a callback that returns `UDP` for `udp`
   - Output: `A Simple TCP and UDP Wrapper`

3. On a line that is entirely uppercase, a word made of initials in the form `A.` or `A.B` (repeated) is left unchanged.
   - Input: `WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM`
   - Output: `Washington, D.C. Should Be Fixed but Might Be a Problem`

4. A word that is `o` or `O`, then `'` or `‘`, then letters, optionally ending in `'s`, is capitalized on both sides of the apostrophe.
   - Input: `my name is o'reilly`
   - Output: `My Name Is O'Reilly`

5. A word that is `d` or `l` (either case), then `'` or `‘`, then letters, optionally ending in `'s`, keeps that first letter lowercase and capitalizes the letter after the apostrophe.
   - Input: `l'grange`
   - Output: `l'Grange`

6. A word starting with `Mc` or `MC`, followed by at least two characters, is rewritten with the prefix `Mc` and the remainder title-cased.
   - Input: `oblon, spivak, mcclelland, maier & neustadt`
   - Output: `Oblon, Spivak, McClelland, Maier & Neustadt`

7. The whole words `Mr`, `Mrs`, `Ms`, and `Dr` (any capitalization, with no period) keep the rest of their letters and receive an initial capital.
   - Input: `mr`
   - Output: `Mr`

8. A word with a period between two letters is left unchanged. This covers domains, dotted initials, and URLs that contain them.
   - Input: `this is just an example.com`
   - Output: `This Is Just an example.com`

9. When the line is not entirely uppercase, a word that already has a capital letter after its first character is left unchanged.
   - Input: `iTunes should be unmolested`
   - Output: `iTunes Should Be Unmolested`

10. A word that is exactly a small word is lowercased.
    - Input: `this v that`
    - Output: `This v That`

11. A word that contains `/` and does not contain `//` is split on each slash. Each piece is title-cased on its own, so a small word at the edge of a piece stays lowercase, and the pieces are joined with `/`.
    - Input: `a title and/or string`
    - Output: `A Title and/or String`

12. A hyphenated word is split on each `-`. Each piece is title-cased on its own, and the pieces are joined with `-`.
    - Input: `end-to-end`
    - Output: `End-to-End`

13. On an entirely uppercase line, a word that the earlier rules did not keep is lowercased before the remaining rules run, so the line comes out in title case.
    - Input: `THIS IS ALL CAPS AND SHOULD BE ADDRESSED`
    - Output: `This Is All Caps and Should Be Addressed`

14. A word longer than two characters that contains only consonants is uppercased as an acronym. The letters `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so a short word such as `St` is capitalized as an ordinary word.
    - Input: `Words with all consonants like cnn are acronyms`
    - Output: `Words With All Consonants Like CNN Are Acronyms`

15. Any other word is capitalized at its first letter. Leading punctuation stays in place.
    - Input: `reading between the lines of steve jobs’s ‘thoughts on music’`
    - Output: `Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’`

16. A token whose first character is not a letter, such as an ordinal, is left unchanged. On an all-caps line it is lowercased first by rule 13.
    - Input: `34th 3rd 2nd`
    - Output: `34th 3rd 2nd`

17. When `small_first_last` is true (the default), a small word at the start of the line is capitalized. Leading punctuation may precede it. A word returned by the callback is skipped.
    - Input: `a thing`
    - Output: `A Thing`

18. When `small_first_last` is true, a small word at the end of the line is capitalized. One trailing punctuation character may follow it. A word returned by the callback is skipped.
    - Input: `Small word at end is nothing to be afraid of`
    - Output: `Small Word at End Is Nothing to Be Afraid Of`

19. The original space characters between words are kept, including tabs and other Unicode spaces. With `normalise_space_characters=True`, the words are joined with a single ordinary space.
    - Input: `text\twith\ttabs`
    - Output (default): `Text\tWith\tTabs`
    - Output (`normalise_space_characters=True`): `Text With Tabs`

20. After the line is assembled, a small word that opens a subphrase is capitalized. A subphrase begins with `:`, `.`, `;`, `?`, `!`, a hyphen, or a dash (`–`, `‒`, `—`, `―`), followed by a space.
    - Input: `Starting Sub-Phrase With a Small Word: a Trick, Perhaps?`
    - Output: `Starting Sub-Phrase With a Small Word: A Trick, Perhaps?`

# Test data
- Generated by titlecase-go/tests/gen.py (seeds 1 and 2) with Python 3.12.16 and the original titlecase code from titlecase-go/environment/repo.
- Each set has 2000 lines and one empty line. The dev and hidden sets share only that empty line.
- sha256 inputs.txt: 56df06b12d06f58accc74d2fa9b226f2e8b7855ec4642805a002b0b0aedd7a75
- sha256 expected.txt: 6ac52d7bdaf1028cf965a115a9b86db59b99b3485c96216b7e5e0d0879c9dc59
- sha256 hidden_inputs.txt: 4cdcd25f249f264372458d72fbdc8b31c1c7d65c239fc8e2dde326d1fc3461d8
- sha256 hidden_expected.txt: c9f6bd89c206d4865e094829d821c02f50328ac4b5008624f3f870c2196444f2
- Checked by scripts/data/verify_data.py: no duplicates, no disallowed characters, rare paths present in both sets.
- Spot-check: 10 of 10 sampled lines match the original.

# Coverage (mutation check, 23 mutants)
- 20 of 23 mutants change at least 18 hidden lines (weakest: vs. 18, via 25, blank-text 28).
- Untested by design: line-breaks (no newlines in input), callback (no callback in the CLI), all-caps-initials (redundant with the inline-period rule on our input set).
- Rare rules (each under 5% of the hidden set): Mc prefix 49, d'/l' 67, O' 84, leading-nonletter 34, all-caps-lower 54 (of 2000 lines).
- Known weakness: reward = (1 + 1 + 4 x behaviour) / 6, so any port with at least 85% of hidden lines right scores 0.9 or more.

# Reference notes
- At this commit the original titlecase source contains no regex look-ahead, look-behind or back-references (searched __init__.py), so the guide's premise does not hold for this repo.
- The answer key was generated without the optional `regex` package (Python's `re` fallback was used).
- A first-draft Go port, written by the agent in one pass from the Python source, matched 2000/2000 dev lines.

# Oracle
- solution/solve.sh is generated by scripts/oracle/build_solve.py from oracle_dev/ (Go port written by an agent from the Python source).
- oracle run: reward 1.0 (behaviour 1.0 on the hidden set, build 1.0, no_python 1.0).
- nop run: reward 0.0.

# Cheat checks (guide weights 1/1/4)
- Cheat A (prints embedded dev answers, keeps .py): 0.167
- Cheat A, deletes .py: 0.334
- Cheat B (echoes input, keeps .py): 0.197
- Cheat B, deletes .py: 0.364
- Finding: build and no_python give 1/3 of the reward to any program that compiles with no .py files. Fix to consider: weights 1/1/12 (cheats then score about 0.14 and 0.18) or gating structure on behaviour.

# Grader hardening
- Before: an exploit that read /tests/data/hidden_expected.txt, and one that ran the original Python via os/exec, both scored 1.0 (jobs cheat-exploitC-prehardening, cheat-exploitD-prehardening).
- Fix: behaviour check rejects forbidden imports (os/exec, syscall, plugin, unsafe, net, cgo, non-stdlib) and go.mod require/replace/use lines, and runs the binary under chroot as uid 65534 in an empty folder.
- After: exploits C, D and E (os.StartProcess variant that bypasses the import rule) score behaviour 0.0 (0.333 total, from build and no_python); oracle still 1.0, nop still 0.0.
- Which layer stopped which exploit is inferred from how each exploit works (C only imports os, so the jail must have stopped it); no layer was disabled on its own to test it.
- Job folders are not committed (jobs/ is gitignored). The evidence is the screenshots/ folder and the numbers above; scripts/ regenerates the rest.

# Known gaps
- Agent runs as root (lint: root-agent). Deferred: the separate verifier container and the jailed binary limit the impact.
- The verifier image contains Python (Reward Kit needs it); the jail has none.
- harbor-rewardkit's own dependencies are not pinned.
- Jail and import rules were validated only on Docker Desktop (Windows host, Linux containers). A kernel-level chroot escape is out of scope.
- This repository is public: tests/data/hidden_* and the full solution are visible. Accepted for this practice task.

# Reproduce
Windows PowerShell, repository root, Python 3.12, Docker running. Run `$env:PYTHONUTF8="1"; $env:PYTHONDONTWRITEBYTECODE="1"` first (UTF-8 for Harbor, and to keep __pycache__ out of environment/repo, which is copied into the image).
- uv pip install "git+https://github.com/ppannuto/python-titlecase@42f43e2de55bf003b286c6f8e8d8b2d26676a167"
- python scripts/data/verify_data.py, then scripts/data/spotcheck.py
- python scripts/oracle/dev_compare.py (2000 equal), then scripts/oracle/build_solve.py (sha256 81e08307...2fc0)
- python scripts/validation/mutation_check.py, predict_cheats.py, build_cheats.py, build_exploits.py, run_cheat.py NAME
- harbor run -p titlecase-go -a oracle (expect 1.0) and -a nop (expect 0.0)