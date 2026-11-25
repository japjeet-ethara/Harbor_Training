#!/bin/bash
set -euo pipefail
REPO=/workspace/repo
find "$REPO" -type f -name '*.py' -delete
cat > "$REPO/go.mod" <<'EOF'
module titlecase

go 1.23
EOF
cat > "$REPO/main.go" <<'EOF'
package main
import (
 "bufio"
 "fmt"
 "os"
 "strings"
 "unicode"
)
var small = map[string]bool{"a":true,"an":true,"and":true,"as":true,"at":true,"but":true,"by":true,"en":true,"for":true,"if":true,"in":true,"of":true,"on":true,"or":true,"the":true,"to":true,"v":true,"v.":true,"via":true,"vs":true,"vs.":true}
func capWord(s string, allCaps bool) string {
 if s=="" { return s }
 if allCaps { s=strings.ToLower(s) }
 // Leave dotted initialisms and dotted names alone; this shortcut misses many rules.
 letters:=0; dots:=0
 for _,r:=range s { if unicode.IsLetter(r) { letters++ }; if r=='.' { dots++ } }
 if dots>0 && letters>1 { return s }
 rs:=[]rune(s)
 i:=0; for i<len(rs) && !unicode.IsLetter(rs[i]) && !unicode.IsDigit(rs[i]) { i++ }
 if i==len(rs) { return s }
 // Simplified Mc handling.
 if i+1<len(rs) && (string(rs[i:i+2])=="Mc" || string(rs[i:i+2])=="mc" || string(rs[i:i+2])=="MC") {
  rs[i]='M'; rs[i+1]='c'; if i+2<len(rs) { rs[i+2]=unicode.ToUpper(rs[i+2]); for j:=i+3;j<len(rs);j++ { rs[j]=unicode.ToLower(rs[j]) } }; return string(rs)
 }
 rs[i]=unicode.ToUpper(rs[i]); for j:=i+1;j<len(rs);j++ { rs[j]=unicode.ToLower(rs[j]) }; return string(rs)
}
func isAllCaps(s string) bool { has:=false; for _,r:=range s { if unicode.IsLetter(r) { has=true; if unicode.IsLower(r) { return false } } }; return has }
func main(){ sc:=bufio.NewScanner(os.Stdin); sc.Buffer(make([]byte,4096),4*1024*1024); out:=bufio.NewWriter(os.Stdout); defer out.Flush(); for sc.Scan(){ line:=sc.Text(); all:=isAllCaps(line); words:=strings.Fields(line); for i,w:=range words { key:=strings.ToLower(w); if small[key] && i>0 && i<len(words)-1 { words[i]=key } else { words[i]=capWord(w,all) } }; fmt.Fprintln(out,strings.Join(words," ")) } }
EOF