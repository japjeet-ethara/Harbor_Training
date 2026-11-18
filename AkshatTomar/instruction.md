## What the repository is

This repository is the Python titlecase project, licensed under the MIT License. Its titlecase function title-cases each line on its own and joins the lines with newlines, using the New York Times small-word list plus `v` and `vs`: `a`, `an`, `and`, `as`, `at`, `but`, `by`, `en`, `for`, `if`, `in`, `of`, `on`, `or`, `the`, `to`, `v`, `v.`, `via`, `vs`, and `vs.`. Small words are lowercased, except that when `small_first_last` is on (the default) a small word that is first or last on the line, or that starts a sub-phrase after a colon, period, semicolon, question mark, exclamation mark, or dash followed by a space, is capitalized; slash-separated and hyphenated parts are title-cased with that first-and-last handling turned off. A callback result replaces a word and is not changed by those first-word and last-word fixes. Fully uppercase lines keep letter-and-period initialisms as written and lowercase any remaining word before later capitalization. The function also handles `d'`/`l'` and `o'` apostrophes (straight or curly, with an optional `'s`), `Mc`/`MC` names, the honorifics `Mr`, `Mrs`, `Ms`, and `Dr`, tokens that contain a letter, a period, and another letter, mixed-case words that already contain a later capital (unless the whole line is uppercase), words split on `/` unless they contain `//`, hyphenated compounds, consonant-only acronyms longer than two letters (`y` counts as a vowel), and ordinary capitalization of any other word, including a capital after leading punctuation. Blank lines are collapsed by default unless `preserve_blank_lines` is true. The original space characters between words are kept unless `normalise_space_characters` is true, in which case words are rejoined with a single ordinary space.

## What to build

Build a Go program in `/workspace/repo`. It must read one title per line from stdin. It must print the titlecased result, one per line.

## Hard rules

- Go standard library only.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## Behaviour

Output must match the original Python `titlecase()` byte for byte, for every input.

## Not checked

- Speed.
- Memory usage.
- Error message wording.

## How it is graded

Hidden automatic tests. Partial score is possible.
