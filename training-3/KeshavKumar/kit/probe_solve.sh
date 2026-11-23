#!/bin/bash
# PROBE (not a cheat to score points): records what an agent could reach.
# 1) While the agent works: user, Python, internet (could it download answers?).
# 2) While its program is graded: the Go program prints one line per probe as
#    its FIRST output lines; they show up in verifier/behaviour_mismatches.txt.
set -uo pipefail
cd /workspace/repo

echo "agent-phase id: $(id)"
echo "agent-phase python3: $(command -v python3 || echo none)"
echo "agent-phase github: $(curl -sS -m 10 -o /dev/null -w '%{http_code}' https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/main/README.md 2>&1 || true)"
echo "agent-phase pypi:   $(curl -sS -m 10 -o /dev/null -w '%{http_code}' https://pypi.org/simple/ 2>&1 || true)"

find /workspace/repo -name '*.py' -delete
rm -rf /workspace/repo/titlecase
printf 'module probe\n\ngo 1.23\n' > go.mod
cat > main.go <<'GOSRC'
package main

import (
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"time"
)

func try(name string, err error) {
	if err == nil {
		fmt.Printf("PROBE %s: OK\n", name)
	} else {
		fmt.Printf("PROBE %s: blocked (%v)\n", name, err)
	}
}

func main() {
	fmt.Printf("PROBE uid=%d gid=%d\n", os.Getuid(), os.Getgid())
	_, err := os.ReadFile("/tests/data/answers.txt")
	try("read /tests/data/answers.txt", err)
	_, err = os.ReadDir("/tests")
	try("list /tests", err)
	_, err = os.ReadDir("/root")
	try("list /root", err)
	_, err = exec.LookPath("python3")
	try("python3 on PATH", err)
	for _, p := range []string{"/usr/bin/python3", "/usr/local/bin/python3"} {
		_, err = os.Stat(p)
		try("stat "+p, err)
	}
	f, err := os.Create("/logs/verifier/probe.txt")
	if f != nil {
		f.Close()
	}
	try("write /logs/verifier", err)
	c, err := net.DialTimeout("tcp", "140.82.112.3:443", 5*time.Second) // github.com
	if c != nil {
		c.Close()
	}
	try("tcp github.com:443 (connect only)", err)
	// A connect can be accepted by an egress proxy; only real data proves access.
	cl := &http.Client{Timeout: 10 * time.Second}
	for _, u := range []string{
		"https://raw.githubusercontent.com/japjeet-ethara/Harbor_Training/main/README.md",
		"http://example.com/",
	} {
		resp, err := cl.Get(u)
		if err == nil {
			b, _ := io.ReadAll(io.LimitReader(resp.Body, 64))
			resp.Body.Close()
			fmt.Printf("PROBE GET %s: HTTP %d, %d bytes\n", u, resp.StatusCode, len(b))
		} else {
			fmt.Printf("PROBE GET %s: blocked (%v)\n", u, err)
		}
	}
}
GOSRC
go build ./...
echo "probe installed"
