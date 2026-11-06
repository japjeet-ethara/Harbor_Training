# Titlecase in Go

## 1. What the repository is

This repository is the MIT-licensed `titlecase` implementation. NOTES.md records the rules that `titlecase` applies. A run of carriage returns or line feeds counts as one line break, and blank lines are dropped unless blank lines are preserved. Whitespace between words, including tabs and other space characters, is kept unless those characters are normalised to a single ordinary space. A callback may replace a word, and later rules leave that replacement as it was returned. On a line with no lowercase letters, a word of dotted initials stays as written, and each remaining word is lowercased before acronym detection and ordinary capitalisation. Apostrophe forms with a leading d or l, and with a leading o, names beginning with Mc, and the words m, mr, mrs, ms, and dr have their own capitalisation. A word that contains a letter, a period, and another letter is left unchanged. On a line that already contains a lowercase letter, a word with a capital later in the word is left unchanged. The small words from the New York Times Manual of Style, plus v and vs, are written in lowercase, except where a small word is capitalised at the start or end of a line or immediately after a subphrase marker and a space. A word that contains a slash but not a double slash, or a hyphen, is split on that mark and each part is titlecased on its own. A word of more than two letters made only of consonants is uppercased; a, e, i, o, u, and y count as vowels, and a consonant-only word of one or two letters is capitalised as an ordinary word. Any other word is capitalised on its first letter, with leading punctuation left in place; when the first word character is a digit, the following letters stay lowercase. Each line is titlecased on its own, and the lines are joined with a newline.

## 2. What to build

Build a Go program in `/workspace/repo`. When it runs, it reads one title per line from standard input and writes the titlecased result to standard output, one title per line.

## 3. Hard rules

- Use the Go standard library only.
- No `.py` files may be left anywhere in the repository.
- `go build ./...` must pass.

## 4. Behaviour

For every input, the output must match the original Python `titlecase()` byte for byte. Use that function’s default arguments: no callback, small words capitalised at the start and end of a line, blank lines not preserved, and space characters not normalised.

## 5. Not checked

Speed, memory, and error-message wording are not checked.

## 6. How it is graded

Hidden automatic tests grade the program. The score can be partial.
