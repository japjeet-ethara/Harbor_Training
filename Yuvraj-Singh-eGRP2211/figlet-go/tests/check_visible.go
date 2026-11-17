package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"
)

type TestCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	dataFile, err := os.Open("/tests/data/visible.jsonl")
	if err != nil {
		fmt.Printf("Error opening /tests/data/visible.jsonl: %v\n", err)
		os.Exit(1)
	}
	defer dataFile.Close()

	scanner := bufio.NewScanner(dataFile)
	buf := make([]byte, 1024*1024)
	scanner.Buffer(buf, 10*1024*1024)

	total := 0
	passed := 0
	failed := 0

	for scanner.Scan() {
		line := scanner.Bytes()
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		var tc TestCase
		if err := json.Unmarshal(line, &tc); err != nil {
			continue
		}
		total++

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, "/tmp/figlet", tc.Args...)
		cmd.Dir = "/workspace/repo"

		var stdout bytes.Buffer
		cmd.Stdout = &stdout
		err := cmd.Run()
		cancel()

		actual := stdout.String()
		if err == nil && actual == tc.Out {
			passed++
		} else {
			failed++
			if failed <= 5 {
				fmt.Printf("=== FAILURE #%d (Case #%d) ===\n", failed, total)
				fmt.Printf("Args: %v\n", tc.Args)
				if err != nil {
					fmt.Printf("Exec error: %v\n", err)
				}
				fmt.Printf("Expected len: %d, Actual len: %d\n", len(tc.Out), len(actual))
				fmt.Printf("--- Expected ---\n%s\n", tc.Out)
				fmt.Printf("--- Actual ---\n%s\n", actual)
				fmt.Println("==============================")
			}
		}
	}

	fmt.Printf("\nSummary: %d / %d passed (%d failures)\n", passed, total, failed)
	if failed > 0 {
		os.Exit(1)
	}
}
