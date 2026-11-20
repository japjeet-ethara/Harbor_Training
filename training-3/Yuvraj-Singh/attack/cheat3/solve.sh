#!/bin/bash
set -e

cat > go.mod << 'GOMOD'
module example.com/titlecase-go

go 1.23
GOMOD

cat > main.go << 'GOMAIN'
package main

import (
"bufio"
"fmt"
"os"
"strings"
)

var small = map[string]bool{
"a":true,"an":true,"and":true,"as":true,"at":true,
"but":true,"by":true,"en":true,"for":true,"if":true,
"in":true,"of":true,"on":true,"or":true,"the":true,
"to":true,"v":true,"v.":true,"via":true,"vs":true,"vs.":true,
}

func titlecase(s string) string {
words := strings.Fields(s)
for i, w := range words {
low := strings.ToLower(w)
if i == 0 || i == len(words)-1 || !small[low] {
if len(w) > 0 {
words[i] = strings.ToUpper(w[:1]) + strings.ToLower(w[1:])
}
} else {
words[i] = low
}
}
return strings.Join(words, " ")
}

func main() {
scanner := bufio.NewScanner(os.Stdin)
scanner.Buffer(make([]byte, 4096), 10*1024*1024)
for scanner.Scan() {
fmt.Println(titlecase(scanner.Text()))
}
}
GOMAIN

find . -name "*.py" -delete

go build -o /tmp/titlecase-go .
/tmp/titlecase-go