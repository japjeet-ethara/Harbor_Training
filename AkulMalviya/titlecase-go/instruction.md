# Titlecase in Go

## 1. What the repository is

This repository is an MIT-licensed Python implementation of title case. Its `titlecase` function rewrites each line into title caps and joins the lines with newline characters. In the middle of a title it keeps these small words lowercase: a, an, and, as, at, but, by, en, for, if, in, of, on, or, the, to, v, v., via, vs, and vs. Consecutive blank lines collapse into a single break unless blank lines are preserved. A callback may replace a word, and that replacement is kept exactly as the callback wrote it, including through the first-and-last small-word fix. On a fully uppercase line, initialisms written as capital letters and periods stay as written when they are one or more of the forms A. or A.B, and the remaining words are lowercased and then passed through the ordinary capitalization rules. A word shaped like d', l', or o' followed by a name, with an optional 's, capitalizes the letter after the apostrophe; o' also capitalizes the o, while d' and l' leave that first letter lowercase. A word starting with Mc or MC capitalizes that prefix and title-cases the remainder. Mr, Mrs, Ms, and Dr capitalize only the first letter, and the rest of the honorific stays as it was. A word with a period between letters is left unchanged. On a line that is not entirely uppercase, a word that already contains an internal capital is left unchanged. Small words are lowercased. A single slash splits a word into pieces that are title-cased and joined again, while a double slash stays in one word. A hyphen splits a word into pieces that are title-cased and joined again, and a small word in the middle of the compound stays lowercase. A word of only consonants, longer than two letters, is uppercased as an acronym; y is a vowel and blocks that rule, and a two-letter word is capitalized as an ordinary word. Any other word capitalizes its first letter, leading punctuation stays in front of that letter, and a word that already starts with a digit keeps that form. The first word and the last word are capitalized even when they are small words, and leading or trailing punctuation stays wrapped around the word; a word frozen by a callback is skipped. A small word that starts a new subphrase is capitalized. The subphrase follows a colon, period, semicolon, question mark, exclamation mark, or dash, and then a space. The original space characters between words are kept unless space normalisation is requested.

## 2. What to build

Build a Go program in `/workspace/repo`. It reads one title per line from standard input and prints the titlecased result, one per line.

## 3. Hard rules

- Use the Go standard library only.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte. Use the default arguments: no callback, small words capitalized at the first and last position, and the original space characters kept.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. A partial score is possible.
