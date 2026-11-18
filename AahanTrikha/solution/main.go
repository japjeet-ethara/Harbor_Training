package main

import (
"bufio"
"fmt"
"os"
"regexp"
"strings"
"unicode"
"unicode/utf8"
)

const small = `a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?`
const punctClass = "!\"“#$%&'‘()*+,\\-–‒—―./:;?@\\[\\]_`{|}~"

var (
smallWords  = regexp.MustCompile(`(?i)^(?:` + small + `)$`)
smallFirst  = regexp.MustCompile(`(?i)^([` + punctClass + `]*)(` + small + `)\b`)
smallLast   = regexp.MustCompile(`(?i)\b(` + small + `)[` + punctClass + `]?$`)
subphrase   = regexp.MustCompile(`([:.;?!\-–‒—―] )(` + small + `)`)
macMc       = regexp.MustCompile(`^([Mm]c|MC)([\p{L}\p{N}_].+)`)
titles      = regexp.MustCompile(`(?i)^(?:m(?:rs?|s)|dr)$`)
inlinePer   = regexp.MustCompile(`(?i)\p{L}\.\p{L}`)
ucElsewhere = regexp.MustCompile(`^[` + punctClass + `]*?\p{L}+\p{Lu}`)
ucInitials  = regexp.MustCompile(`^(?:\p{Lu}\.|\p{Lu}\.\p{Lu})+$`)
aposSecond  = regexp.MustCompile(`(?i)^[dol]['‘]\p{L}+(?:['s]{2})?$`)
capFirst    = regexp.MustCompile(`^[` + punctClass + `]*?\p{L}`)
)

func capitalize(s string) string {
r := []rune(s)
if len(r) == 0 {
return s
}
r[0] = unicode.ToUpper(r[0])
for i := 1; i < len(r); i++ {
r[i] = unicode.ToLower(r[i])
}
return string(r)
}

func allConsonants(s string) bool {
if utf8.RuneCountInString(s) <= 2 {
return false
}
for _, c := range s {
if !strings.ContainsRune("bcdfghjklmnpqrstvwxz", unicode.ToLower(c)) {
return false
}
}
return true
}

func conv(w string, allCaps bool) string {
if allCaps && ucInitials.MatchString(w) {
return w
}
if aposSecond.MatchString(w) {
r := []rune(w)
if len(r) >= 3 {
if !strings.ContainsRune("aeiouAEIOU", r[0]) {
r[0] = unicode.ToLower(r[0])
} else {
r[0] = unicode.ToUpper(r[0])
}
r[2] = unicode.ToUpper(r[2])
}
return string(r)
}
if m := macMc.FindStringSubmatch(w); m != nil {
return capitalize(m[1]) + tcLine(m[2], true)
}
if titles.MatchString(w) {
r := []rune(w)
r[0] = unicode.ToUpper(r[0])
return string(r)
}
if inlinePer.MatchString(w) || (!allCaps && ucElsewhere.MatchString(w)) {
return w
}
if smallWords.MatchString(w) {
return strings.ToLower(w)
}
if strings.Contains(w, "/") && !strings.Contains(w, "//") {
p := strings.Split(w, "/")
for i := range p {
p[i] = tcLine(p[i], false)
}
return strings.Join(p, "/")
}
if strings.Contains(w, "-") {
p := strings.Split(w, "-")
for i := range p {
p[i] = tcLine(p[i], false)
}
return strings.Join(p, "-")
}
if allCaps {
w = strings.ToLower(w)
}
if allConsonants(w) {
return strings.ToUpper(w)
}
return capFirst.ReplaceAllStringFunc(w, strings.ToUpper)
}

func tcLine(s string, firstLast bool) string {
allCaps := strings.ToUpper(s) == s

var words, spaces []string
var cur []rune
for _, r := range s {
if unicode.IsSpace(r) {
words = append(words, string(cur))
cur = cur[:0]
spaces = append(spaces, string(r))
} else {
cur = append(cur, r)
}
}
words = append(words, string(cur))

tc := make([]string, len(words))
for i, w := range words {
tc[i] = conv(w, allCaps)
}

if firstLast && len(tc) > 0 {
tc[0] = smallFirst.ReplaceAllStringFunc(tc[0], func(m string) string {
g := smallFirst.FindStringSubmatch(m)
return g[1] + capitalize(g[2])
})
n := len(tc) - 1
tc[n] = smallLast.ReplaceAllStringFunc(tc[n], capitalize)
}

var b strings.Builder
for i := range tc {
b.WriteString(tc[i])
if i < len(spaces) {
b.WriteString(spaces[i])
}
}
return subphrase.ReplaceAllStringFunc(b.String(), func(m string) string {
g := subphrase.FindStringSubmatch(m)
return g[1] + capitalize(g[2])
})
}

func main() {
sc := bufio.NewScanner(os.Stdin)
sc.Buffer(make([]byte, 1024*1024), 1024*1024)
out := bufio.NewWriter(os.Stdout)
defer out.Flush()
for sc.Scan() {
fmt.Fprintln(out, tcLine(sc.Text(), true))
}
}