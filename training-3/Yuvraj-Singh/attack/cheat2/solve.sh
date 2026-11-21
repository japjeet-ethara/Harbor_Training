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
)

func main() {
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
fmt.Println(scanner.Text())
}
}
GOMAIN

find . -name "*.py" -delete

go build -o /tmp/titlecase-go .