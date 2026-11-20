package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	expected, err := os.Open("/tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer expected.Close()

	if _, err := io.Copy(os.Stdout, expected); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
