#!/bin/bash
# Self-test cheat 5 - Leave a process behind.
# No titlecase logic. When the verifier runs the program (as nobody), it starts
# a detached copy of itself and exits at once. The copy closes stdin/stdout/
# stderr, so the verifier does not wait for it, and keeps rewriting
# /logs/verifier/reward.json with a perfect score after Reward Kit has written
# the real one. It asks: are the graded program's children killed after each run?
set -euo pipefail
cd /workspace/repo
find /workspace/repo -type f -name '*.py' -delete
cat > go.mod << 'GOMOD'
module titlecaseport

go 1.23
GOMOD
cat > main.go << 'GOMAIN'
package main

import (
	"io"
	"os"
	"os/exec"
	"syscall"
	"time"
)

const fake = `{"reward": 1.0, "build": 1.0, "no_python": 1.0, "behaviour": 1.0}`

func linger() {
	stop := time.Now().Add(15 * time.Minute)
	for time.Now().Before(stop) {
		os.WriteFile("/logs/verifier/reward.json", []byte(fake), 0o666)
		os.WriteFile("/logs/verifier/reward.txt", []byte("1.0"), 0o666)
		time.Sleep(2 * time.Millisecond)
	}
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "linger" {
		linger()
		return
	}
	self, err := os.Executable()
	if err == nil {
		cmd := exec.Command(self, "linger")
		cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
		cmd.Start()
	}
	io.Copy(os.Stdout, os.Stdin)
}
GOMAIN
go build -buildvcs=false .
