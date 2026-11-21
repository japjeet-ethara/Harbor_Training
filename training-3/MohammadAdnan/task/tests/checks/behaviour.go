package main

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"
)

const nobody = 65534

// splitLines matches Python bytes.splitlines(): breaks on \n, \r and \r\n, no trailing empty line.
func splitLines(b []byte) [][]byte {
	var out [][]byte
	start := 0
	for i := 0; i < len(b); i++ {
		if b[i] == '\n' || b[i] == '\r' {
			out = append(out, b[start:i])
			if b[i] == '\r' && i+1 < len(b) && b[i+1] == '\n' {
				i++
			}
			start = i + 1
		}
	}
	if start < len(b) {
		out = append(out, b[start:])
	}
	return out
}

// checkBehaviour feeds the hidden inputs (100,000 titles, one per line, given as one text as
// instruction.md says) to the program and returns the share of answer lines matched exactly, and
// how many matched. inputs.txt / answers.txt come from kit/answers.py (titlecase WITHOUT regex).
func checkBehaviour() (float64, int) {
	inputs, err1 := os.ReadFile(filepath.Join(dataDir, "inputs.txt"))
	expected, err2 := os.ReadFile(filepath.Join(dataDir, "answers.txt"))
	if err1 != nil || err2 != nil {
		fmt.Println("behaviour: cannot read hidden data:", err1, err2)
		return 0, 0
	}
	want := splitLines(expected)
	if len(want) == 0 {
		return 0, 0
	}

	runDir, err := os.MkdirTemp("", "run")
	if err != nil {
		return 0, 0
	}
	defer os.RemoveAll(runDir)
	_ = os.Chmod(runDir, 0o777)

	ctx, cancel := context.WithTimeout(context.Background(), 300*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, binary)
	cmd.Dir = runDir
	cmd.Env = []string{"PATH=/usr/bin:/bin", "HOME=" + runDir, "LANG=C.UTF-8"}
	cmd.Stdin = bytes.NewReader(inputs)
	var out bytes.Buffer
	cmd.Stdout = &out
	if os.Geteuid() == 0 {
		cmd.SysProcAttr = &syscall.SysProcAttr{Credential: &syscall.Credential{Uid: nobody, Gid: nobody}}
	}
	if err := cmd.Run(); err != nil {
		fmt.Println("behaviour: program failed:", err)
		return 0, 0
	}

	got := splitLines(out.Bytes())
	matched, shown := 0, 0
	for i, w := range want {
		if i < len(got) && bytes.Equal(got[i], w) {
			matched++
		} else if shown < 3 {
			shown++
			fmt.Printf("behaviour: line %d differs\n", i+1)
		}
	}
	fmt.Printf("behaviour: %d/%d hidden lines match\n", matched, len(want))
	return float64(matched) / float64(len(want)), matched
}
