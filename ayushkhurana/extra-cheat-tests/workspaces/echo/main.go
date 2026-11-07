package main

import (
	"io"
	"os"
)

// Prints every input line unchanged.
func main() { io.Copy(os.Stdout, os.Stdin) }
