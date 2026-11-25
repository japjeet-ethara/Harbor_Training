package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"os"
)

func run(input io.Reader, output io.Writer) error {
	reader := bufio.NewReader(input)
	writer := bufio.NewWriter(output)
	for {
		record, err := reader.ReadString('\n')
		if err != nil && !errors.Is(err, io.EOF) {
			return err
		}
		if len(record) != 0 {
			if record[len(record)-1] == '\n' {
				record = record[:len(record)-1]
				if len(record) != 0 && record[len(record)-1] == '\r' {
					record = record[:len(record)-1]
				}
			}
			if _, err := writer.WriteString(titlecase(record, true)); err != nil {
				return err
			}
			if err := writer.WriteByte('\n'); err != nil {
				return err
			}
		}
		if errors.Is(err, io.EOF) {
			return writer.Flush()
		}
	}
}

func main() {
	if err := run(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
