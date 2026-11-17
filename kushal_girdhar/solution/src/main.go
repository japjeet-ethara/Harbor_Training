package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
)

func transform(input io.Reader, output io.Writer) error {
	reader := bufio.NewReader(input)
	writer := bufio.NewWriter(output)
	for {
		record, err := reader.ReadString('\n')
		if len(record) != 0 {
			if strings.HasSuffix(record, "\n") {
				record = strings.TrimSuffix(strings.TrimSuffix(record, "\n"), "\r")
			}
			if _, writeErr := writer.WriteString(titlecase(record, true) + "\n"); writeErr != nil {
				return writeErr
			}
		}
		if errors.Is(err, io.EOF) {
			return writer.Flush()
		}
		if err != nil {
			return err
		}
	}
}

func main() {
	if err := transform(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
