# titlecase-go

Port the Python titlecase library in `/workspace/repo` to Go. That Python source is the specification. For every input, the Go result must match the original Python implementation byte for byte.

## Program

Read standard input one title per line. Write exactly one transformed title for each input line, and write nothing else. Keep the same number of lines: an empty input line produces an empty output line. Do not skip, join, or collapse lines. Transform each line on its own.

Use the library defaults for each line: no callback, no custom abbreviation list, no host word list, and no space normalisation.

Preserve every behavior the Python source actually implements. That includes punctuation, whitespace, capitalization, apostrophes, hyphens, slashes, small words, abbreviations, initials, acronyms, all-caps text, Unicode, and the other edge cases in that source. Follow the behavior used when the optional third-party `regex` package is not installed.

## Constraints

- Use the Go standard library only. Do not add module dependencies.
- Put a Go module at `/workspace/repo`. It must compile with `go build ./...`.
- Include a `main` package that performs the stdin and stdout behavior above.
- Do not leave any `.py` file anywhere under `/workspace/repo`.
- Do not change this input/output contract. Exact output is required.
