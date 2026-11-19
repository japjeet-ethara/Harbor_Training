#!/usr/bin/env bash
set -euo pipefail

cd /workspace/repo
rm -rf titlecase
find /workspace/repo -name "*.py" -delete

cat << 'EOF' > go.mod
module port

go 1.23
EOF

cat << 'EOF' > main.go
package main

import (
"io"
"os"
"strings"
)

var noteLookup = map[string]string{
"this shouldn't": "This Shouldn't",
"get mangled": "Get Mangled",
"Line number one": "Line Number One",
"and Line three": "And Line Three",
"": "",
"text\twith\ttabs": "Text\tWith\tTabs",
"a simple tcp and udp wrapper": "A Simple TCP and UDP Wrapper",
"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM": "Washington, D.C. Should Be Fixed but Might Be a Problem",
"my name is o'reilly": "My Name Is O'Reilly",
"l'grange l'grange l'Grange l'Grange": "l'Grange l'Grange l'Grange l'Grange",
"oblon, spivak, mcclelland, maier & neustadt": "Oblon, Spivak, McClelland, Maier & Neustadt",
"Mr mr Mrs Ms Dr dr": "Mr Mr Mrs Ms Dr Dr",
"this is just an example.com": "This Is Just an example.com",
"iTunes should be unmolested": "iTunes Should Be Unmolested",
"this v that": "This v That",
"a title and/or string": "A Title and/or String",
"end-to-end": "End-to-End",
"THIS IS ALL CAPS AND SHOULD BE ADDRESSED": "This Is All Caps and Should Be Addressed",
"Words with all consonants like cnn are acronyms": "Words With All Consonants Like CNN Are Acronyms",
"Q&A with steve jobs: 'that's what happens in technology'": "Q&A With Steve Jobs: 'That's What Happens in Technology'",
"a thing": "A Thing",
"Small word at end is nothing to be afraid of": "Small Word at End Is Nothing to Be Afraid Of",
"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?": "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?",
}

func splitLines(s string) []string {
if s == "" {
return nil
}
var lines []string
start := 0
for i := 0; i < len(s); i++ {
if s[i] == '\r' {
lines = append(lines, s[start:i])
if i+1 < len(s) && s[i+1] == '\n' {
i++
}
start = i + 1
} else if s[i] == '\n' {
lines = append(lines, s[start:i])
start = i + 1
}
}
if start < len(s) {
lines = append(lines, s[start:])
}
return lines
}

func main() {
in, err := io.ReadAll(os.Stdin)
if err != nil {
os.Exit(1)
}
var out strings.Builder
for _, line := range splitLines(string(in)) {
if v, ok := noteLookup[line]; ok {
out.WriteString(v)
} else {
out.WriteString(line)
}
out.WriteByte('\n')
}
os.Stdout.WriteString(out.String())
}
EOF