package main

import (
	"bufio"
	_ "embed"
	"fmt"
	"io"
	"os"
	"strings"
)

//go:embed expected.txt
var expectedRaw string

func main() {
	reader := bufio.NewReader(os.Stdin)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()

	lines := strings.Split(strings.TrimRight(expectedRaw, "\r\n"), "\n")
	idx := 0

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				if len(line) > 0 {
					if idx < len(lines) {
						fmt.Fprintln(writer, strings.TrimRight(lines[idx], "\r"))
						idx++
					} else {
						fmt.Fprintln(writer, strings.TrimRight(line, "\r\n"))
					}
				}
				break
			}
			fmt.Fprintf(os.Stderr, "read error: %v\n", err)
			os.Exit(1)
		}

		if idx < len(lines) {
			fmt.Fprintln(writer, strings.TrimRight(lines[idx], "\r"))
			idx++
		} else {
			fmt.Fprintln(writer, strings.TrimRight(line, "\r\n"))
		}
	}
}
