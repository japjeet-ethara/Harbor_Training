# Titlecase in Go

## 1. What the repository is

`/workspace/repo` is the Python package `titlecase` 2.4.1. The implementation lives in `titlecase/__init__.py`: a line-oriented, whitespace-preserving rewrite of John Gruber's `titlecase.pl` by way of Stuart Colville. It does not title-case by splitting on words in the Unicode sense. It splits on newline characters, then on individual whitespace characters, then applies an ordered list of special cases to each token. The public entry point is `titlecase(text, callback=None, small_first_last=True, preserve_blank_lines=False, normalise_space_characters=False)`. Also public are `set_small_word_list` and `create_wordlist_filter_from_file`. The console script is `titlecase = titlecase.__init__:cmd`. `NOTES.md` describes how that code actually runs, including quirks the README does not mention. When `regex` is installed, patterns use Unicode properties; otherwise the standard-library `re` fallback is used, and the two engines disagree on some inputs. Match the `regex` behaviour.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from stdin and prints the titlecased result, one per line.

## 3. Hard rules

Use the Go standard library only. No `.py` files may be left anywhere in the repository. `go build ./...` must pass.

## 4. Behaviour

The output must match the original Python `titlecase()` byte for byte, for every input.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. The score can be partial.
