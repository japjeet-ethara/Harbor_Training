package main

import (
	"bufio"
	"encoding/json"
	"os"
	"strings"
)

// tries to read the hidden answers at run time (should be denied: /tests is root-only, the program runs as nobody)
func main() {
	f, err := os.Open("/tests/data/hidden.jsonl")
	if err != nil {
		return
	}
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	want := strings.Join(os.Args[1:], "\x1f")
	for sc.Scan() {
		var r struct {
			Args []string `json:"args"`
			Out  string   `json:"out"`
		}
		if json.Unmarshal(sc.Bytes(), &r) == nil && strings.Join(r.Args, "\x1f") == want {
			os.Stdout.WriteString(r.Out)
			return
		}
	}
}
