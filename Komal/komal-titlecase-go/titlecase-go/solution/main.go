package main

import (
	"fmt"
	"os"

	"komal/titlecase/internal/format"
	"komal/titlecase/internal/records"
)

func main() {
	if err := records.Run(os.Stdin, os.Stdout, format.Titlecase); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
