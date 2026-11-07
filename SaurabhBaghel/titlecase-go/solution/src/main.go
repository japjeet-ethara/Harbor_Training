package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
)

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1<<20)
	out := bufio.NewWriterSize(os.Stdout, 1<<20)
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			if line[len(line)-1] == '\n' {
				line = line[:len(line)-1]
			}
			if len(line) > 0 && line[len(line)-1] == '\r' {
				line = line[:len(line)-1]
			}
			fmt.Fprintln(out, TitleCase(line))
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			os.Exit(1)
		}
	}
	if err := out.Flush(); err != nil {
		os.Exit(1)
	}
}
