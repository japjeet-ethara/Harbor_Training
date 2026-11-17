package main

import (
	"strings"
	"unicode/utf8"
)

var smallWords = [...]string{
	"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in",
	"of", "on", "or", "the", "to", "v.", "v", "via", "vs.", "vs",
}

func isSmall(word string) bool {
	folded := asciiFolded(word)
	for _, small := range smallWords {
		if folded == small {
			return true
		}
	}
	return false
}

func prefixEnd(word, pattern string) (int, bool) {
	at := 0
	for _, wanted := range pattern {
		if at == len(word) {
			return 0, false
		}
		ch, width := utf8.DecodeRuneInString(word[at:])
		if foldASCII(ch) != wanted {
			return 0, false
		}
		at += width
	}
	return at, true
}

func capitalizeFirstSmall(word string) string {
	start := skipPunctuation(word)
	tail := word[start:]
	for _, small := range smallWords {
		end, match := prefixEnd(tail, small)
		if match && wordAt(tail, end-lastRuneWidth(tail, end)) != wordAt(tail, end) {
			return word[:start] + lowercase(tail[:end], true) + tail[end:]
		}
	}
	return word
}

func lastRuneWidth(s string, end int) int {
	_, width := utf8.DecodeLastRuneInString(s[:end])
	return width
}

func capitalizeLastSmall(word string) string {
	previousWasWord := false
	for start, ch := range word {
		isWord := properties(ch)&wordChar != 0
		if !previousWasWord && isWord {
			tail := word[start:]
			for _, small := range smallWords {
				end, match := prefixEnd(tail, small)
				if match && endOrSinglePunctuation(tail[end:]) {
					return word[:start] + lowercase(tail, true)
				}
			}
		}
		previousWasWord = isWord
	}
	return word
}

func endOrSinglePunctuation(tail string) bool {
	ch, width := utf8.DecodeRuneInString(tail)
	return tail == "" || width == len(tail) && punctuation(ch)
}

func capitalizeSubphrases(line string) string {
	var result strings.Builder
	written := 0
	for at := 0; at+2 < len(line); {
		ch, width := utf8.DecodeRuneInString(line[at:])
		at += width
		if !strings.ContainsRune(":.;?!-–‒—―", ch) || at == len(line) || line[at] != ' ' {
			continue
		}
		for _, small := range smallWords {
			if strings.HasPrefix(line[at+1:], small) {
				start := at + 1
				end := start + len(small)
				result.WriteString(line[written:start])
				result.WriteString(lowercase(line[start:end], true))
				written = end
				at = end
				break
			}
		}
	}
	if written == 0 {
		return line
	}
	result.WriteString(line[written:])
	return result.String()
}
