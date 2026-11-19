package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
)

type entry struct {
	Input  string `json:"input"`
	Output string `json:"output"`
}

func main() {
	data, err := os.ReadFile("/workspace/repo/lookup.json")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	var entries []entry
	if err := json.Unmarshal(data, &entries); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	answers := make(map[string]string, len(entries))
	for _, item := range entries {
		answers[item.Input] = item.Output
	}

	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 4*1024*1024)
	writer := bufio.NewWriter(os.Stdout)
	defer writer.Flush()
	for scanner.Scan() {
		if answer, ok := answers[scanner.Text()]; ok {
			fmt.Fprintln(writer, answer)
		} else {
			fmt.Fprintln(writer, "UNKNOWN")
		}
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
