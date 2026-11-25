# Harbor Titlecase-Go experiments

## Objective and task architecture

The task ports `python-titlecase` v2.4.1 to a root-package Go program. Harbor collects `/workspace/repo`, runs the submitted solution script there, then runs the verifier in a separate container. The program reads one title per input line and must reproduce the original `titlecase()` output byte-for-byte. The task allows standard-library Go only and requires that no `.py` files remain in the collected repository.

The verifier entry point invokes RewardKit. Its build check runs `go build -o /dev/null ./...`; its no-Python check recursively rejects `.py` files and builds again; its behavior check builds the program, feeds the hidden input fixture, and counts exact output-line matches. The visible and hidden fixtures each contain 2,000 disjoint cases generated deterministically from the original Python function.

## Reward and findings

The reward is `(build + no_python + 4 * behaviour) / 6`. Build and no-Python can therefore contribute one third of the reward even when behavior is zero. That happened in Cheats 2 and 3 and in Cheat 4's first Harbor run. This rewards packaging and compilation separately, but it also allows a nonfunctional implementation to receive a substantial score. A behavioral threshold or multiplicative gate would better align reward with the task's main objective.

## Reference behavior

The reference is the regex-enabled branch of `attack/target/environment/python-titlecase/titlecase/__init__.py`, with default arguments. The rules are order-sensitive:

1. Determine whether the whole line is uppercase; preserve uppercase initial sequences in that case.
2. Apply special apostrophe forms, Mc names, and the `Mr`/`Mrs`/`Ms`/`Dr` title rule.
3. Preserve tokens with an inline letter-period-letter pattern, and preserve mixed-case tokens when the uppercase regex matches.
4. Lowercase exact small words; recursively titlecase slash-separated tokens (unless they contain `//`) and hyphen-separated tokens with boundary small-word adjustment disabled.
5. Lowercase all-uppercase ordinary words, uppercase ASCII consonant-only tokens longer than two characters, and otherwise uppercase the first letter following configured punctuation.
6. Apply small-word capitalization at the title's first and last token, then capitalize small words after the configured punctuation-plus-space subphrase pattern.

These rules cover the generator's plain and small-word cases, acronyms and consonant tokens, brands and mixed case, apostrophe and Mc names, titles, initials and dotted tokens, URLs, hyphen and slash forms, wrappers, Unicode letters, digits, punctuation, and edge lines. The reference preserves original whitespace. It is not a general editorial title-style rule set.

## Experiments

| Experiment | Strategy | Public accuracy | Build | No-Python | Behavior | Reward | Finding |
|---|---|---:|---:|---:|---:|---:|---|
| Cheat 1 | Copy stdin to stdout; remove Python files | Not measured | 1.000 | 1.000 | 0.002 | 0.3347 | Structural checks earned reward; accidental exact matches gave a small behavior score. |
| Cheat 2 | `strings.Fields` and basic capitalization | Not measured | 1.000 | 1.000 | 0.000 | 0.3333 | Ordinary title casing did not match the reference's whitespace and token rules. |
| Cheat 3 | Preserve spaces and tabs with basic word rules | 620/2,000 (31.0%) | 1.000 | 1.000 | 0.000 | 0.3333 | Whitespace preservation alone did not reproduce ordered Unicode and punctuation rules. |
| Cheat 4, initial Harbor run | Reference-rule Go port, but LF output for CRLF fixtures | 100% after local input normalization | 1.000 | 1.000 | 0.000 | 0.3333 | Byte comparison exposed fixture line-ending differences. |
| Cheat 4, corrected rerun | Same Go port, preserving input line-ending style | 2,000/2,000 (100%) | 1.000 | 1.000 | 1.000 | 1.0000 | Exact reference behavior and fixture byte conventions passed. |

Cheat 1 also had earlier runs: one failed because its reward file was missing (no score), and another scored 0.000 behavior / 0.3333 reward. The table records its successful verified run at 0.3347.

Cheat 4's original hand-written implementation, preserved in the `.initial.bak` files, scored 604/2,000 (30.2%) on the public fixtures when rebuilt and measured. The final reference-rule port raised that to 2,000/2,000.

## Final Cheat 4 implementation

`attack/cheat4/solution/solve.sh` is the delivered, self-contained final implementation. Its heredoc writes the Go module and source into `/workspace/repo`, removes Python files from that collected repository, and builds the program. The Go implementation uses rune-level predicates and transformations to reproduce the Python regex rules without third-party packages. It preserves whitespace and handles UTF-8 letters, apostrophes, initials, titles, URLs, slash and hyphen recursion, acronyms, punctuation, and title boundaries in reference order.

During development, a local-check Go source and synchronization script were used to compare and copy the implementation into the Harbor heredoc. Those local-check files are not included in the submission. The submitted solution is self-contained in `solution/solve.sh`. The program accepts LF and CRLF input and mirrors that line-ending style on output. This is needed because the checked-in Windows fixture files use CRLF and the Harbor byte comparator retains each expected line's carriage return.

During development, the initial Cheat 4 source measured 604/2,000 (30.2%) on the public fixtures; the improved local implementation measured 2,000/2,000. A local byte-level diagnostic also matched all 2,000 available hidden-fixture lines. These are historical local measurements: the local-check source, synchronization script, and initial-source backups are not included, so those local comparisons cannot be independently reproduced from the submitted files. The official hidden evaluation is the successful Harbor rerun recorded above.

The verifier logic, fixtures, and reward weights were not changed. The copied Cheat 4 `tests/test.sh` uses LF line endings while the original target copy uses CRLF; their text content is otherwise identical.

## Lessons and limitations

- Byte-level evaluation includes whitespace and line endings, not just capitalization. A local comparator based on `splitlines()` can hide CRLF differences that Harbor's byte split exposes.
- Ordered regex behavior is more important than curated brand and acronym exceptions.
- Keep one implementation source and synchronize generated execution files mechanically.
- The compatibility claim is scoped to the task's stated input contract and fixtures. Inputs outside those constraints may expose differences between Python's `regex` Unicode tables and Go's standard-library Unicode tables.
- Harbor's first run returned 0 behavior because output used LF against CRLF expected data. After mirroring CRLF, Harbor completed with no verifier errors and full reward.
