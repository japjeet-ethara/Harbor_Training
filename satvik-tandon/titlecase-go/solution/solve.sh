#!/bin/bash
set -euo pipefail
cd /workspace/repo
find . -type f -name '*.py' -delete
rm -f setup.py pyproject.toml setup.cfg tox.ini
cat > go.mod <<'EOF'
module titlecasego
go 1.23
EOF
cat > main.go <<'EOF'
package main
import("bufio";"fmt";"os";"regexp";"strings";"unicode")
var small=map[string]bool{"a":true,"an":true,"and":true,"as":true,"at":true,"but":true,"by":true,"en":true,"for":true,"if":true,"in":true,"of":true,"on":true,"or":true,"the":true,"to":true,"v":true,"v.":true,"via":true,"vs":true,"vs.":true}
var initials=regexp.MustCompile(`^(?:[A-Z]\.|[A-Z]\.[A-Z])+$`);var honor=regexp.MustCompile(`(?i)^(m((rs?)|s)|dr)$`);var mac=regexp.MustCompile(`(?i)^mc([[:alnum:]_].+)$`)
func up(s string)string{for i,r:=range s{if unicode.IsLetter(r){return s[:i]+string(unicode.ToUpper(r))+s[i+len(string(r)):]}};return s}
func cap(s string)string{return up(strings.ToLower(s))}
func inline(s string)bool{r:=[]rune(s);for i:=1;i+1<len(r);i++{if r[i]=='.'&&unicode.IsLetter(r[i-1])&&unicode.IsLetter(r[i+1]){return true}};return false}
func innerUpper(s string)bool{seen:=false;for _,r:=range s{if unicode.IsLetter(r){if seen&&unicode.IsUpper(r){return true};seen=true}};return false}
func consonants(s string)bool{n:=0;for _,r:=range strings.ToLower(s){if !unicode.IsLetter(r)||strings.ContainsRune("aeiouy",r){return false};n++};return n>2}
func apost(s string)bool{r:=[]rune(s);if len(r)<4||!strings.ContainsRune("dolDOL",r[0])||(r[1]!='\''&&r[1]!='‘'){return false};for _,x:=range r[2:]{if !unicode.IsLetter(x)&&x!='\''&&x!='s'&&x!='S'{return false}};return true}
func word(s string,all bool)string{if s==""{return s};if all&&initials.MatchString(s){return s};if apost(s){r:=[]rune(s);if strings.ContainsRune("aeiouAEIOU",r[0]){r[0]=unicode.ToUpper(r[0])}else{r[0]=unicode.ToLower(r[0])};r[2]=unicode.ToUpper(r[2]);return string(r)};if m:=mac.FindStringSubmatch(s);len(m)>0{return "Mc"+title(m[1],false)};if honor.MatchString(s){return up(s)};if inline(s)||(!all&&innerUpper(s)){return s};if small[strings.ToLower(s)]{return strings.ToLower(s)};if strings.Contains(s,"/")&&!strings.Contains(s,"//"){p:=strings.Split(s,"/");for i:=range p{p[i]=title(p[i],false)};return strings.Join(p,"/")};if strings.Contains(s,"-"){p:=strings.Split(s,"-");for i:=range p{p[i]=title(p[i],false)};return strings.Join(p,"-")};if all{s=strings.ToLower(s)};if consonants(s){return strings.ToUpper(s)};return up(s)}
func title(line string,edge bool)string{all:=strings.ToUpper(line)==line;p:=strings.Split(line," ");for i:=range p{p[i]=word(p[i],all)};if edge&&len(p)>0{if small[strings.ToLower(p[0])]{p[0]=cap(p[0])};j:=len(p)-1;core:=strings.TrimRight(p[j],"!\"#$%&'()*+,-./:;?@[\\]_`{|}~");if small[strings.ToLower(core)]{p[j]=cap(core)+p[j][len(core):]}};out:=strings.Join(p," ");for _,mark:=range []string{": ",". ","; ","? ","! ","- "}{pos:=0;for pos<len(out){rel:=strings.Index(out[pos:],mark);if rel<0{break};i:=pos+rel;start:=i+len(mark);end:=start;for end<len(out)&&out[end]!=' '{end++};if small[strings.ToLower(out[start:end])]{w:=cap(out[start:end]);out=out[:start]+w+out[end:];pos=start+len(w)}else{pos=start}}};return out}
func main(){s:=bufio.NewScanner(os.Stdin);for s.Scan(){fmt.Println(title(s.Text(),true))}}
EOF
gofmt -w main.go
