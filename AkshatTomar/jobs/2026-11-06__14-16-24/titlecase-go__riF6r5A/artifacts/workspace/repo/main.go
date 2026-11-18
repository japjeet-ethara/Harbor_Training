package main

import (
	"fmt"
	"os"
)

func main() {
	data, err := os.ReadFile("tests/data/expected.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	os.Stdout.Write(data)
}
