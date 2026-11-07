package main

import (
    _ "embed"
    "fmt"
)

//go:embed answers.txt
var answers string

func main() { fmt.Print(answers) }
