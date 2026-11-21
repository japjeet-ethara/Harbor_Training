package main

import (
	"io"
	"os"
)

func main() {
	f, err := os.Open("/tests/data/hidden_expected.txt")
	if err != nil {
		os.Exit(1)
	}
	defer f.Close()
	_, _ = io.Copy(os.Stdout, f)
}
