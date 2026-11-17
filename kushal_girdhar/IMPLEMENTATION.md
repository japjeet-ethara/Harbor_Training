# Implementation

## Reference runtime and stream contract

The reference is python-titlecase 2.4.1 at commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`. Dataset generation and differential tests ran the upstream default function using CPython 3.12.14 and Unicode 15.0.0. The optional `regex` package was unavailable. The upstream import used `re`, which changes several patterns compared with the optional backend. The reference loader checks all three runtime choices before generating answers.

The Go entry point in `solution/src/main.go` reads bytes through a buffered reader. It treats LF and CRLF as record endings, retains blank records and an unterminated final record, and emits each transformed record followed by LF. A zero-byte stream emits zero bytes. The transformation preserves internal record bytes according to Python's rules, including the default collapse of runs of embedded CR and LF into internal LF. The frozen scoring data contains only records with LF delimiters and without embedded CR or LF.

## Transformation

`engine.go` scans UTF-8 once to track each word and separator as byte ranges. Every Python whitespace match contributes a separator and a word slot, including zero-length words. This detail controls small words at the edges when spaces lead or trail the line. Each word runs through the ordered checks in `formatWord`. The Mc rule calls the engine with edge handling enabled. Slash and hyphen compounds start fresh calls with edge handling disabled and fresh all-caps detection for each part. Slash processing precedes ASCII hyphens. A double slash skips the slash stage. Small-word edge passes run after token transformation. Subphrase capitalization runs on the rejoined line.

`small.go` applies prefix, suffix, boundary, and subphrase rules with byte positions and decoded rune boundaries. It matches the upstream alternation order, optional punctuation, restricted punctuation alphabets, and the difference between case-insensitive edge patterns and case-sensitive subphrases.

`casing.go` and `python_tables.go` use CPython's full single-character upper, lower, and title mappings, including multi-rune results. The generated property ranges capture Python word characters and whitespace plus the cased and case-ignorable distinctions that matter for Greek final sigma. A backward state and a forward scan implement sigma context across ignorable code points. The engine uses the fallback regex backend's four Unicode additions to ASCII ignore-case matches. It never relies on Go Unicode category or casing equivalence.

## Frozen corpus

`tests/gen.py` calls `random.seed(1)`. It builds 16 coverage cells of 125 titles per split. Each cell has 31 titles from each of release, incident, network, and documentation plus one title assigned by rotation. Each domain therefore contributes 500 per split. Different subject pools represent distinct engineering work across the splits. The generator rejects duplicate inputs and duplicate reference outputs across the complete corpus, including casing variants that collapse to the same answer. It shuffles each split after selection. It obtains every frozen answer by calling the pinned Python function.

`tools/validate_reference.py` checks all frozen answers, five visible spot checks, split disjointness, exact framing in a distinct protocol suite, and a separate seeded fuzz stream. It mixes token-shaped cases, compound layouts, whitespace, targeted Unicode blocks, and uniformly drawn scalar values. Its test records are generated independently of the corpus templates.

## Verifier and replay

Harbor builds the agent from `environment/` and the verifier from `tests/`. The build contexts are separate and use explicit Docker file allowlists. The agent receives the upstream project. Harbor hands off the candidate's repository as an artifact to a fresh verifier container. The verifier image contains the hidden split and a hash-locked installation of Reward Kit. Both runtime network policies are offline.

The grader inventories the transferred tree, rejects unsafe entries, checks for Python files, then runs `go build ./...` and builds the root executable. Commands use a clean environment, a scratch directory, disabled CGO and Go dependency downloads, and deadlines. The Linux launcher clears supplementary groups, drops to UID/GID 65534, sets no-new-privileges, and applies resource limits. A preflight verifies that this UID cannot read the tests or write to the verifier log directory. The candidate process receives the hidden inputs over a pipe. Behavior compares UTF-8 bytes at each position. A complete stream with a wrong line gets per-line partial credit. Missing LF, extra rows, truncation, and process failure score zero for behavior.

Reward Kit writes the aggregate and three criterion scores to `/logs/verifier/reward.json` and writes criterion diagnostics to `reward-details.json`. Build and Python removal each carry weight 1. Python removal awards credit only if the build passes. Behavior carries weight 4. An unchanged checkout scores zero by design. A build-only replay leaves the upstream Python files, so an exact visible replay with zero hidden matches earns 1/6. A replay that also removes Python can earn 1/3 from the two mandated structural checks even with zero hidden matches.

## Hardest observed rule and proposed extension

The first Go comparison exposed the vowel branch in apostrophe names. The reference folds `d` and `l` to lowercase but capitalizes `o`, and applies the name rule before internal capitals. The mismatch and successful rerun are recorded in the evidence.

A useful hardening change would add a separately frozen protocol suite to supplement the existing 2,000 hidden titles. It could combine trailing whitespace, CRLF, and long records with adjacent empty records and contextual Unicode casing. The current protocol suite already checks these features locally.
