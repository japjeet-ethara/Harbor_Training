package main

import (
"bufio"
"flag"
"fmt"
"io"
"os"
"regexp"
"strings"
"unicode"
"unicode/utf8"
)

const smallPat = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
const punctCls = `!"\x{201c}#$%&'\x{2018}()*+,./:;?@[\\\]_` + "`" + `{|}~\x{2013}\x{2012}\x{2014}\x{2015}-`

var smallWordsRe = regexp.MustCompile(`(?i)^(` + smallPat + `)$`)
var smallFirstRe = regexp.MustCompile(`(?i)^([` + punctCls + `]*)(` + smallPat + `)\b`)
var smallLastRe = regexp.MustCompile(`(?i)\b(` + smallPat + `)[` + punctCls + `]?$`)
var subphraseRe = regexp.MustCompile(`([:.;?!\-\x{2013}\x{2012}\x{2014}\x{2015}] )(` + smallPat + `)`)
var macMcRe = regexp.MustCompile(`^([Mm]c|MC)([\p{L}\p{N}_].+)`)
var mrMrsMsDrRe = regexp.MustCompile(`(?i)^((m((rs?)|s))|Dr)$`)
var inlinePeriod = regexp.MustCompile(`(?i)[\p{L}\p{N}_][.][\p{L}\p{N}_]`)
var ucElsewhere = regexp.MustCompile(`^[` + punctCls + `]*?[a-zA-Z]+[A-Z]`)
var capfirstRe = regexp.MustCompile(`^[` + punctCls + `]*?([\p{L}\p{N}_])`)
var ucInitialsRe = regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`)

func pyCapitalize(s string) string {
if s == "" {
return ""
}
r, size := utf8.DecodeRuneInString(s)
return strings.ToUpper(string(r)) + strings.ToLower(s[size:])
}

func isPySpace(r rune) bool {
if unicode.IsSpace(r) {
return true
}
switch r {
case '\x1c', '\x1d', '\x1e', '\x1f', '\u2028', '\u2029':
return true
}
return false
}

func pySplitSpace(line string) ([]string, []string) {
var words []string
var spaces []string
var cur strings.Builder
for _, r := range line {
if isPySpace(r) {
words = append(words, cur.String())
cur.Reset()
spaces = append(spaces, string(r))
} else {
cur.WriteRune(r)
}
}
words = append(words, cur.String())
return words, spaces
}

func isAsciiConsonants(w string) bool {
if len(w) <= 2 {
return false
}
for i := 0; i < len(w); i++ {
c := w[i]
if c >= 'A' && c <= 'Z' {
c += 'a' - 'A'
}
if c < 'a' || c > 'z' {
return false
}
switch c {
case 'a', 'e', 'i', 'o', 'u', 'y':
return false
}
}
return true
}

func matchAposSecond(w string) bool {
rs := []rune(w)
if len(rs) < 3 {
return false
}
first := unicode.ToLower(rs[0])
if first != 'd' && first != 'o' && first != 'l' {
return false
}
if rs[1] != '\'' && rs[1] != '\u2018' {
return false
}
body := rs[2:]
isPyWord := func(r rune) bool {
return r == '_' || unicode.IsLetter(r) || unicode.IsDigit(r)
}
if len(body) >= 3 && (body[len(body)-2] == '\'' || body[len(body)-2] == 's' || body[len(body)-2] == 'S') &&
(body[len(body)-1] == '\'' || body[len(body)-1] == 's' || body[len(body)-1] == 'S') {
allW := true
for _, r := range body[:len(body)-2] {
if !isPyWord(r) {
allW = false
break
}
}
if allW {
return true
}
}
for _, r := range body {
if !isPyWord(r) {
return false
}
}
return true
}

func titlecaseCore(text string, smallFirstLast bool) string {
lines := strings.Split(text, "\n")
processed := make([]string, 0, len(lines))

for _, line := range lines {
line = strings.TrimSuffix(line, "\r")
allCaps := strings.ToUpper(line) == line
words, spaces := pySplitSpace(line)
tcLine := make([]string, 0, len(words))

for _, word := range words {
if allCaps {
if ucInitialsRe.MatchString(word) {
tcLine = append(tcLine, word)
continue
}
}

if matchAposSecond(word) {
rs := []rune(word)
if !strings.ContainsRune("aeiouAEIOU", rs[0]) {
rs[0] = unicode.ToLower(rs[0])
} else {
rs[0] = unicode.ToUpper(rs[0])
}
rs[2] = unicode.ToUpper(rs[2])
tcLine = append(tcLine, string(rs))
continue
}

if m := macMcRe.FindStringSubmatch(word); m != nil {
tcLine = append(tcLine, pyCapitalize(m[1])+titlecaseCore(m[2], true))
continue
}

if mrMrsMsDrRe.MatchString(word) {
rs := []rune(word)
rs[0] = unicode.ToUpper(rs[0])
tcLine = append(tcLine, string(rs))
continue
}

if inlinePeriod.MatchString(word) || (!allCaps && ucElsewhere.MatchString(word)) {
tcLine = append(tcLine, word)
continue
}

if smallWordsRe.MatchString(word) {
tcLine = append(tcLine, strings.ToLower(word))
continue
}

if strings.Contains(word, "/") && !strings.Contains(word, "//") {
parts := strings.Split(word, "/")
for i, p := range parts {
parts[i] = titlecaseCore(p, false)
}
tcLine = append(tcLine, strings.Join(parts, "/"))
continue
}

if strings.Contains(word, "-") {
parts := strings.Split(word, "-")
for i, p := range parts {
parts[i] = titlecaseCore(p, false)
}
tcLine = append(tcLine, strings.Join(parts, "-"))
continue
}

if allCaps {
word = strings.ToLower(word)
}

if isAsciiConsonants(word) {
tcLine = append(tcLine, strings.ToUpper(word))
continue
}

loc := capfirstRe.FindStringIndex(word)
if loc != nil {
tcLine = append(tcLine, strings.ToUpper(word[:loc[1]])+word[loc[1]:])
} else {
tcLine = append(tcLine, word)
}
}

if smallFirstLast && len(tcLine) > 0 {
if m := smallFirstRe.FindStringSubmatchIndex(tcLine[0]); m != nil {
p1 := tcLine[0][m[2]:m[3]]
p2 := tcLine[0][m[4]:m[5]]
tcLine[0] = p1 + pyCapitalize(p2) + tcLine[0][m[1]:]
}
lastIdx := len(tcLine) - 1
if m := smallLastRe.FindStringIndex(tcLine[lastIdx]); m != nil {
tcLine[lastIdx] = tcLine[lastIdx][:m[0]] + pyCapitalize(tcLine[lastIdx][m[0]:m[1]]) + tcLine[lastIdx][m[1]:]
}
}

var joined strings.Builder
for i := range tcLine {
joined.WriteString(tcLine[i])
if i < len(spaces) {
joined.WriteString(spaces[i])
}
}
res := joined.String()

res = subphraseRe.ReplaceAllStringFunc(res, func(match string) string {
sub := subphraseRe.FindStringSubmatch(match)
return sub[1] + pyCapitalize(sub[2])
})

processed = append(processed, res)
}

return strings.Join(processed, "\n")
}

func main() {
inputFile := flag.String("f", "", "File to read from")
flag.String("input-file", "", "File to read from")
outputFile := flag.String("o", "", "File to write to")
flag.String("output-file", "", "File to write to")
flag.String("w", "", "Wordlist")
flag.String("wordlist", "", "Wordlist")
flag.Bool("preserve-blank-lines", false, "Preserve blank lines")
flag.Parse()

var reader io.Reader = os.Stdin
if *inputFile != "" && *inputFile != "-" {
if f, err := os.Open(*inputFile); err == nil {
defer f.Close()
reader = f
}
}

var writer io.Writer = os.Stdout
if *outputFile != "" && *outputFile != "-" {
if f, err := os.Create(*outputFile); err == nil {
defer f.Close()
writer = f
}
}

args := flag.Args()
if len(args) > 0 {
fmt.Fprintln(writer, titlecaseCore(strings.Join(args, " "), true))
return
}

scanner := bufio.NewScanner(reader)
scanner.Buffer(make([]byte, 0, 1024*1024), 10*1024*1024)
out := bufio.NewWriter(writer)
for scanner.Scan() {
out.WriteString(titlecaseCore(scanner.Text(), true))
out.WriteByte('\n')
}
out.Flush()
}