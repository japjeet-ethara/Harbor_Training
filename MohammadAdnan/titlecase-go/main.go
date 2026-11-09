package main

import (
	"io"
	"os"
)

func main() {
	input, err := io.ReadAll(os.Stdin)
	if err != nil {
		os.Exit(1)
	}
	output := Titlecase(string(input))
	os.Stdout.WriteString(output)
}
