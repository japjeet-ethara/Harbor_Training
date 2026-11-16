// showdiff runs a built figlet program over a cases file and shows the first
// cases that differ (args, expected, actual). Developer tool for Step 6; it is
// not part of the exam and is never copied into /tests.
//
//	cd /workspace/repo && go build -o /tmp/figlet . && go run /path/to/showdiff.go -bin /tmp/figlet -cases visible.jsonl
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

type testCase struct {
	Args []string `json:"args"`
	Out  string   `json:"out"`
}

func main() {
	bin := flag.String("bin", "/tmp/figlet", "program to test")
	cases := flag.String("cases", "visible.jsonl", "jsonl file with {\"args\": [...], \"out\": \"...\"}")
	max := flag.Int("max", 5, "how many differing cases to show")
	flag.Parse()

	f, err := os.Open(*cases)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 1<<24)

	total, bad, shown := 0, 0, 0
	for sc.Scan() {
		var c testCase
		if err := json.Unmarshal(sc.Bytes(), &c); err != nil {
			fmt.Fprintln(os.Stderr, "bad line:", err)
			os.Exit(2)
		}
		total++
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		cmd := exec.CommandContext(ctx, *bin, c.Args...)
		var stdout bytes.Buffer
		cmd.Stdout = &stdout
		runErr := cmd.Run()
		cancel()
		got := stdout.String()
		if got == c.Out && runErr == nil {
			continue
		}
		bad++
		if shown < *max {
			shown++
			fmt.Printf("---- case %d: %q\n", total, c.Args)
			if runErr != nil {
				fmt.Println("program error:", runErr)
			}
			want, have := strings.Split(c.Out, "\n"), strings.Split(got, "\n")
			n := len(want)
			if len(have) > n {
				n = len(have)
			}
			for i := 0; i < n; i++ {
				var w, h string
				if i < len(want) {
					w = want[i]
				}
				if i < len(have) {
					h = have[i]
				}
				mark := "  "
				if w != h {
					mark = "!!"
				}
				fmt.Printf("%s exp|%s|\n%s got|%s|\n", mark, w, mark, h)
			}
		}
	}
	fmt.Printf("\n%d of %d cases differ\n", bad, total)
	if bad > 0 {
		os.Exit(1)
	}
}
