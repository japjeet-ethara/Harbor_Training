// Author tool: runs a built twin on a .jsonl case file and prints the first N
// cases whose output differs, with args, expected and actual.
//
//	go run tools/first_diffs.go /tmp/figlet tests/data/visible.jsonl 5
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Println("usage: first_diffs BINARY CASES.jsonl [N]")
		os.Exit(2)
	}
	limit := 5
	if len(os.Args) > 3 {
		limit, _ = strconv.Atoi(os.Args[3])
	}
	f, err := os.Open(os.Args[2])
	if err != nil {
		panic(err)
	}
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 16<<20)
	total, bad := 0, 0
	for sc.Scan() {
		var c struct {
			Args []string `json:"args"`
			Out  string   `json:"out"`
		}
		if json.Unmarshal(sc.Bytes(), &c) != nil {
			continue
		}
		total++
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, os.Args[1], c.Args...)
		cmd.Dir = "/"
		got, err := cmd.Output()
		cancel()
		if err == nil && string(got) == c.Out {
			continue
		}
		bad++
		if bad <= limit {
			a, _ := json.Marshal(c.Args)
			fmt.Printf("=== case %d args %s (err %v)\n--- expected\n%s--- actual\n%s\n",
				total, a, err, show(c.Out), show(string(got)))
		}
	}
	fmt.Printf("%d of %d cases differ\n", bad, total)
}

// show marks line ends so trailing spaces are visible.
func show(s string) string {
	return strings.ReplaceAll(s, "\n", "|\n")
}
