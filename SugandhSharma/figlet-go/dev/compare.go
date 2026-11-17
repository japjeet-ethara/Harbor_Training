// compare runs /tmp/figlet on every case of a .jsonl file and shows the first five that differ.
//
//	go run compare.go /task/tests/data/visible.jsonl
//
// It ends with status 1 when a case differs.
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

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("usage: go run compare.go CASES.jsonl [PROGRAM]")
		os.Exit(2)
	}
	program := "/tmp/figlet"
	if len(os.Args) > 2 {
		program = os.Args[2]
	}
	file, err := os.Open(os.Args[1])
	if err != nil {
		fmt.Println(err)
		os.Exit(2)
	}
	defer file.Close()

	total, wrong, shown := 0, 0, 0
	lines := bufio.NewScanner(file)
	lines.Buffer(make([]byte, 1024*1024), 64*1024*1024)
	for lines.Scan() {
		var c testCase
		if err := json.Unmarshal(lines.Bytes(), &c); err != nil {
			fmt.Println("bad line:", err)
			os.Exit(2)
		}
		total++
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, program, c.Args...)
		cmd.Dir = "/"
		var stdout bytes.Buffer
		cmd.Stdout = &stdout
		runErr := cmd.Run()
		cancel()
		if stdout.String() == c.Out {
			continue
		}
		wrong++
		if shown < 5 {
			shown++
			fmt.Printf("---- case %d: args %q (%v)\nexpected:\n%s\nactual:\n%s\n", total, c.Args, runErr, c.Out, stdout.String())
		}
	}
	fmt.Printf("%d of %d cases match; %d differ\n", total-wrong, total, wrong)
	if wrong > 0 {
		os.Exit(1)
	}
}
