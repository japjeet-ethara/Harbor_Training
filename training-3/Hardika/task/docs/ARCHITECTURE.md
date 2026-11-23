# Architecture

| File | Responsibility |
| --- | --- |
| `solution/go/main.go` | Read delimited records, remove a CR when followed by a record LF, and write byte exact UTF-8 output with one final LF per result. |
| `solution/go/engine.go` | Split logical lines, limit the all-caps decision to each line, reconstruct separators, and apply edge and subphrase rewrites. |
| `solution/go/rules.go` | Define rule precedence and conditions. Return the rune span required by a rewrite. |
| `solution/go/rewrite.go` | Execute rewrites and recurse into the token interpreter using the reference’s per-branch edge setting. |
| `solution/go/unicode.go` | Look up pinned character properties and Python casing mappings, including context-sensitive lowercase sigma. |
| `tools/unicode_tables.py` | Derive range-compressed character properties and sparse casing maps for Unicode scalar values. |

Go regular expressions cover line breaks, the literal Mc prefix, ASCII-folded small words and honorifics, and the case-sensitive subphrase pattern. The matcher implements word boundaries and positional capture rules with explicit code-point checks. It follows the upstream small-word alternative order and handles the optional period before checking an edge boundary. Each rewriting rule stops that token’s scan when it matches. Recursive calls recompute the all-caps condition from the fragment, and the top-level first/last and subphrase passes still run in the reference order.

The table generator queries the installed regex package for letter, uppercase-letter, word, whitespace and consonant classes. It probes case-insensitive matches against ASCII pattern literals. It derives full upper, lower and title mappings from CPython string methods, plus two context predicates from CPython’s final-sigma behavior. This captures CPython’s Unicode 15.0.0 casing and the separately versioned regex Unicode tables. The Go command embeds the generated data as Go literals, so it can run without Python or external files.

The stream contract is UTF-8. An embedded CR other than the CR in a consumed CRLF delimiter is preserved for the upstream logical-line split. The protocol checks cover this special case separately. Invalid UTF-8 and inputs for which Python itself raises an exception fall outside byte-agreement comparisons.
