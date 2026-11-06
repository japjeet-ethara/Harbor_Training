package main

import (
	_ "embed"
	"os"
)

//go:embed answers.txt
var answers []byte

func main() {
	_, _ = os.Stdout.Write(answers)
}
