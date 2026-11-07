package main

import (
	"bufio"
	"io"
	"os"
	"strings"
)

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer out.Flush()

	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			line = strings.TrimSuffix(line, "\n")
			out.WriteString(titlecase(line, true))
			out.WriteString("\n")
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			os.Exit(1)
		}
	}
}
