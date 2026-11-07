# Titlecase in Go

## 1. What the repository is

This repository is the MIT-licensed Python `titlecase` package. Its `titlecase()` function changes text to Title Caps and lowercases a fixed set of small words from the New York Times Manual of Style, plus `vs` and `v`: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`. Consecutive line breaks collapse into one unless blank lines are preserved. A non-empty callback result is kept as given. On an entirely uppercase line, a word of initials (an uppercase letter and a period, repeated) stays as written, and any word that is still being processed is lowercased before the acronym check and ordinary capitalization. A word that starts with `d` or `l`, an apostrophe (`'` or `‘`), and a name keeps a lowercase first letter, capitalizes the letter after the apostrophe, and leaves the rest of the spelling, including a trailing `'s`. A word that starts with `o` and an apostrophe capitalizes both `o` and the letter after the apostrophe and leaves the rest of the spelling. A word that starts with `Mc` or `MC`, followed by at least two more word characters, is written with the prefix `Mc` and the remainder titlecased. The exact words `Mr`, `Mrs`, `Ms`, and `Dr` force the first letter to uppercase and leave the remaining letters as they were. A word that contains a letter, a period, and another letter stays unchanged. When the line is not entirely uppercase, a word that already has an uppercase letter after other letters stays unchanged. A word that contains `/` and does not contain `//` is split on each slash, each piece is titlecased with first-and-last small-word capitalization turned off, and the pieces are joined with `/`. A hyphenated word is split on each `-`, each piece is titlecased the same way, and the pieces are joined with `-`. A word longer than two letters that contains only consonants is uppercased as an acronym; `a`, `e`, `i`, `o`, `u`, and `y` count as vowels, so a two-letter word is capitalized as an ordinary word. Any other word capitalizes its first letter and leaves the rest unchanged, including leading punctuation and a leading digit. With `small_first_last` enabled, a small word at the start of the line is capitalized, and a small word at the end of the line is capitalized even when one trailing punctuation character follows it; punctuation before the first word stays in place, and a callback result is left as written. After the line is joined, a small word that follows a subphrase separator and a space is capitalized. The separator is one of `:`, `.`, `;`, `?`, `!`, `-`, `–`, `‒`, `—`, or `―`. Original space characters between words stay in place unless space normalisation is on, in which case the words of each line are joined with a single ordinary space.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from standard input and writes the titlecased result to standard output, one per line.

## 3. Hard rules

- Use the Go standard library only.
- Leave no `.py` files anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte. Call it with its default arguments: `callback=None`, `small_first_last=True`, `preserve_blank_lines=False`, and `normalise_space_characters=False`.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. A result that is correct for only some inputs receives a partial score.
