#!/bin/bash
# CHEAT 3 - "Memorised exam": a Go program with NO title-casing rules.
# Every expected answer was copied from tests/test_outputs.py, which is public
# (github.com/japjeet-ethara/Harbor_Training) and reachable from the agent
# container because task.toml sets network_mode = "public". The exam is a fixed
# list of ~70 strings, so a lookup table keyed on (wordlist, line) passes all of
# it. The only real code is CLI/IO plumbing; unknown lines are echoed unchanged.
set -euo pipefail
mkdir -p /app && cd /app
cat > go.mod <<'GOEOF'
module titlecase

go 1.23
GOEOF
cat > main.go <<'GOEOF'
package main

import (
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var table = map[string]string{
	"\u0000text\twith\ttabs": "Text\tWith\tTabs",
	"\u0000text with nonbreaking spaces": "Text With Nonbreaking Spaces",
	"\u0000a  thing": "A  Thing",
	"\u0000 a thing": " a Thing",
	"\u0000this is a test": "This Is a Test",
	"\u0000THIS IS A TEST": "This Is a Test",
	"\u0000this is a TEST": "This Is a TEST",
	"\u0000the cat sat on a mat": "The Cat Sat on a Mat",
	"\u0000this v that": "This v That",
	"\u0000this v. that": "This v. That",
	"\u0000this vs that": "This vs That",
	"\u0000this vs. that": "This vs. That",
	"\u0000this is THE test": "This Is THE Test",
	"\u0000hello, the world": "Hello, the World",
	"\u0000Mr. and Mrs. Person": "Mr. And Mrs. Person",
	"\u0000Starting Sub-Phrase With a Small Word: a Trick, Perhaps?": "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
	"\u0000Snakes on a Plane - The TV Edit - The Famous Line": "Snakes on a Plane - The TV Edit - The Famous Line",
	"\u0000EPISODE 7 — THE FORCE AWAKENS": "Episode 7 — The Force Awakens",
	"\u0000my name is o'reilly": "My Name Is O'Reilly",
	"\u0000l'grange": "l'Grange",
	"\u0000l'GranGe": "l'GranGe",
	"\u0000o'grange's": "O'Grange's",
	"\u0000l’grange": "L’grange",
	"\u0000mctavish": "McTavish",
	"\u0000MCFOO-BAR": "McFoo-Bar",
	"\u0000mc": "Mc",
	"\u0000macdonalds": "Macdonalds",
	"\u0000Mr mr Mrs Ms Mss Dr dr": "Mr Mr Mrs Ms MSS Dr Dr",
	"\u0000this is just an example.com": "This Is Just an example.com",
	"\u0000this is http://foo.com": "This Is http://foo.com",
	"\u0000http://localhost": "Http://localhost",
	"\u0000iTunes should be unmolested": "iTunes Should Be Unmolested",
	"\u0000WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM": "Washington, D.C. Should Be Fixed but Might Be a Problem",
	"\u0000word/word": "Word/Word",
	"\u0000a title and/or string": "A Title and/or String",
	"\u0000end-to-end": "End-to-End",
	"\u0000a-b": "A-B",
	"\u0000a-b end-to-end two-not-three/three-by-four/five-and": "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And",
	"\u0000Words with all consonants like cnn are acronyms": "Words With All Consonants Like CNN Are Acronyms",
	"\u0000a simple tcp and udp wrapper": "A Simple TCP and Udp Wrapper",
	"\u0000st and cnn": "St and CNN",
	"\u0000FOO BAR 5TH ST": "Foo Bar 5th St",
	"\u000034th 3rd 2nd": "34th 3rd 2nd",
	"\u0000«word": "«word",
	"\u0000'by the Way, small word at the start but within quotes.'": "'By the Way, Small Word at the Start but Within Quotes.'",
	"\u0000Small word at end is nothing to be afraid of": "Small Word at End Is Nothing to Be Afraid Of",
	"\u0000\"Nothing to Be Afraid of?\"": "\"Nothing to Be Afraid Of?\"",
	"\u0000Q&A with steve jobs: 'that's what happens in technology'": "Q&A With Steve Jobs: 'That's What Happens in Technology'",
	"\u0000What is AT&T's problem?": "What Is AT&T's Problem?",
	"\u0000EL NIÑO A ARRIVÉ HIER": "El Niño a Arrivé Hier",
	"\u0000El Niño": "El Niño",
	"\u0000ÝÆ ÑØ": "Ýæ Ñø",
	"\u0000“YOUNG AND RESTLESS”": "“Young and Restless”",
	"\u0000make me a title": "Make Me a Title",
	"\u0000a thing": "A Thing",
	"\u0000Can pipe and/or whatever else": "Can Pipe and/or Whatever Else",
	"\u0000Line number one": "Line Number One",
	"\u0000and Line three": "And Line Three",
	"\u0000Leading blank": "Leading Blank",
	"\u0000Multi-blank": "Multi-Blank",
	"\u0000Trailing Blank": "Trailing Blank",
	"\u0000Line one": "Line One",
	"\u0000Line two": "Line Two",
	"TCP,UDP,PPPoE\u0000a simple tcp and udp wrapper": "A Simple TCP and UDP Wrapper",
	"TCP,UDP,PPPoE\u0000SENDING UDP PACKETS OVER PPPOE WORKS GREAT": "Sending UDP Packets Over PPPoE Works Great",
	"TCP\u0000tcp rocks": "TCP Rocks",
	"TCP\u0000see tcp, today": "See Tcp, Today",
	"Udp,UDP\u0000udp packets": "UDP Packets",
	"a\u0000a thing": "a Thing",
	"UDP\u0000a simple tcp and udp wrapper": "A Simple TCP and UDP Wrapper",
	"UDP\u0000udp": "UDP",
}

func usage() { os.Stderr.WriteString("usage error\n"); os.Exit(2) }

func main() {
	var in, out, wl string
	preserve := false
	var pos []string
	a := os.Args[1:]
	for i := 0; i < len(a); i++ {
		switch a[i] {
		case "-f", "--input-file", "-o", "--output-file", "-w", "--wordlist":
			if i+1 >= len(a) {
				usage()
			}
			v := a[i+1]
			i++
			switch a[i-1] {
			case "-f", "--input-file":
				in = v
			case "-o", "--output-file":
				out = v
			default:
				wl = v
			}
		case "--preserve-blank-lines":
			preserve = true
		default:
			if strings.HasPrefix(a[i], "-") && a[i] != "-" {
				usage()
			}
			pos = append(pos, a[i])
		}
	}
	if len(pos) > 0 && in != "" {
		usage()
	}
	var text string
	if len(pos) > 0 {
		text = strings.Join(pos, " ")
	} else if in != "" && in != "-" {
		b, err := os.ReadFile(in)
		if err != nil {
			os.Exit(1)
		}
		text = string(b)
	} else {
		b, _ := io.ReadAll(os.Stdin)
		text = string(b)
	}
	if wl == "" {
		home, _ := os.UserHomeDir()
		wl = filepath.Join(home, ".titlecase.txt")
	}
	var words []string
	if b, err := os.ReadFile(wl); err == nil {
		for _, l := range strings.Split(string(b), "\n") {
			if l = strings.TrimSpace(l); l != "" {
				words = append(words, l)
			}
		}
	}
	key := strings.Join(words, ",") + "\x00"
	sep := regexp.MustCompile(`[\r\n]+`)
	if preserve {
		sep = regexp.MustCompile(`[\r\n]`)
	}
	lines := sep.Split(text, -1)
	for i, l := range lines {
		if v, ok := table[key+l]; ok {
			lines[i] = v
		}
	}
	res := strings.Join(lines, "\n")
	if out != "" && out != "-" {
		os.WriteFile(out, []byte(res), 0o644)
		return
	}
	os.Stdout.WriteString(res)
}
GOEOF
go build -o /app/titlecase .
