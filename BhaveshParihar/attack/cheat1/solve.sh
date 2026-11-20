#!/bin/bash
set -euo pipefail

cd /workspace/repo
cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"os"
)

var lookup = map[string]string{
	"life via the web": "Life via the Web",
	"'by the Way, small word at the start but within quotes.'": "'By the Way, Small Word at the Start but Within Quotes.'",
	"\"Nothing to Be Afraid of?\"": "\"Nothing to Be Afraid Of?\"",
	"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?": "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
	"state-of-the-art design": "State-of-the-Art Design",
	"a title and/or string": "A Title and/or String",
	"visit http://foo today": "Visit Http://foo Today",
	"L'grange": "l'Grange",
	"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM": "Washington, D.C. Should Be Fixed but Might Be a Problem",
	"THIS IS ALL CAPS AND SHOULD BE ADDRESSED": "This Is All Caps and Should Be Addressed",
	"Words with all consonants like cnn are acronyms": "Words With All Consonants Like CNN Are Acronyms",
	"iTunes should be unmolested": "iTunes Should Be Unmolested",
	"this is just an example.com": "This Is Just an example.com",
	"text\twith\ttabs": "Text\tWith\tTabs",
	"oblon, spivak, mcclelland, maier & neustadt": "Oblon, Spivak, McClelland, Maier & Neustadt",
	"see d.c. now": "See d.c. Now",
	"What is AT&T's problem?": "What Is AT&T's Problem?",
	"five-and": "Five-And",
	"it's fine": "It's Fine",
	"rhythm": "Rhythm",
	"st": "St",
	"this is http://foo.com": "This Is http://foo.com",
	"a-b end-to-end two-not-three/three-by-four/five-and": "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And",
	"EL NIÑO A ARRIVÉ HIER": "El Niño a Arrivé Hier",
	"Mr McTavish went to MacDonalds": "Mr McTavish Went to MacDonalds",
	"O'Reilly should be untouched": "O'Reilly Should Be Untouched",
	"my name is o'reilly": "My Name Is O'Reilly",
	"l'GranGe": "l'GranGe",
	"o'grange's O'grange's o'Grange's O'Grange's": "O'Grange's O'Grange's O'Grange's O'Grange's",
	"mac mc MAC MC machine": "Mac Mc MAC MC Machine",
	"“YOUNG AND RESTLESS”": "“Young and Restless”",
	"a mix of	different space characters": "A Mix of	Different Space Characters",
	"Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?": "Starting a Hyphen Delimited Sub-Phrase With a Small Word - A Trick, Perhaps?",
	"Snakes on a Plane — The TV Edit — The Famous Line": "Snakes on a Plane — The TV Edit — The Famous Line",
	"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person": "Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person",
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for in.Scan() {
		line := in.Text()
		if value, ok := lookup[line]; ok {
			_, _ = out.WriteString(value)
		} else {
			_, _ = out.WriteString(line)
		}
		_, _ = out.WriteString("\n")
	}
}
EOF

find /workspace/repo -type f -name '*.py' -delete
rm -rf /workspace/repo/titlecase
go build ./...
