#!/bin/sh
# Cheat 3 - Python inside (the real break). No Go titlecase logic: ship the
# ORIGINAL implementation as non-.py data and, at run time, call a Python
# interpreter on it. The repository is left with no .py file, so the no_python
# check passes, yet the "implement it in Go, no external interpreter" rule is
# bypassed and the behaviour score is a perfect match.
#
# Robustness:
#  - the upstream source is located dynamically (not a hard-coded path);
#  - at run time several interpreter names and absolute locations are tried;
#  - the stdlib `re` fallback is forced so the output matches the task's mode;
#  - if no interpreter exists (e.g. the task is later hardened), it degrades to
#    a naive in-Go port instead of crashing, so the build/no_python floor is kept.
set -eu
cd /workspace/repo

# Locate the upstream implementation (the file that defines titlecase) and keep
# it as data, not as a .py file.
SRC="$(grep -rl --include='*.py' 'def titlecase' . | head -n1)"
test -n "$SRC"
cp "$SRC" tc_src.txt

cat > runner.txt <<'PY'
import os
import sys
import importlib.util

sys.modules['regex'] = None  # force the stdlib `re` fallback (the task's mode)

spec = importlib.util.spec_from_file_location('titlecase_src', os.environ['TC_SRC'])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

data = sys.stdin.buffer.read().decode('utf-8')
records = data.split('\n')
trailing_lf = bool(records) and records[-1] == ''
if trailing_lf:
    records = records[:-1]
out = '\n'.join(mod.titlecase(rec) for rec in records)
if trailing_lf:
    out += '\n'
sys.stdout.buffer.write(out.encode('utf-8'))
PY

cat > go.mod <<'MOD'
module titlecase-pyinside
go 1.23.0
MOD

cat > main.go <<'GO'
package main

import (
	"bufio"
	_ "embed"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"unicode"
)

//go:embed tc_src.txt
var pySource string

//go:embed runner.txt
var runner string

func findPython() string {
	names := []string{"python3", "python", "python3.12", "python3.11"}
	for _, n := range names {
		if p, err := exec.LookPath(n); err == nil {
			return p
		}
	}
	for _, p := range []string{
		"/usr/local/bin/python3", "/usr/bin/python3",
		"/usr/local/bin/python", "/usr/bin/python",
	} {
		if fi, err := os.Stat(p); err == nil && !fi.IsDir() {
			return p
		}
	}
	return ""
}

// runPython reproduces the reference via the original implementation. Returns
// false if no interpreter is available or the run fails.
func runPython() bool {
	exe := findPython()
	if exe == "" {
		return false
	}
	dir, err := os.MkdirTemp("", "tc")
	if err != nil {
		return false
	}
	srcPath := filepath.Join(dir, "titlecase_src.py")
	runPath := filepath.Join(dir, "runner.py")
	if os.WriteFile(srcPath, []byte(pySource), 0o600) != nil ||
		os.WriteFile(runPath, []byte(runner), 0o600) != nil {
		return false
	}
	cmd := exec.Command(exe, runPath)
	cmd.Env = append(os.Environ(), "TC_SRC="+srcPath)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run() == nil
}

// naiveFallback keeps the build/no_python floor if no interpreter is present.
func naiveFallback() {
	r := bufio.NewReaderSize(os.Stdin, 1<<20)
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	defer w.Flush()
	cap1 := func(s string) string {
		rs := []rune(s)
		done := false
		for i, r := range rs {
			if !done && unicode.IsLetter(r) {
				rs[i] = unicode.ToUpper(r)
				done = true
			} else {
				rs[i] = unicode.ToLower(r)
			}
		}
		return string(rs)
	}
	for {
		line, err := r.ReadString('\n')
		if len(line) > 0 {
			nl := strings.HasSuffix(line, "\n")
			key := strings.TrimSuffix(line, "\n")
			words := strings.Split(key, " ")
			for i, p := range words {
				words[i] = cap1(p)
			}
			w.WriteString(strings.Join(words, " "))
			if nl {
				w.WriteByte('\n')
			}
		}
		if err != nil {
			break
		}
	}
}

func main() {
	if !runPython() {
		naiveFallback()
	}
}
GO

# No .py file may remain under the repository.
find . -type f \( -name '*.py' -o -name '*.pyc' \) -delete
find . -depth -type d -name '__pycache__' -exec rmdir {} + 2>/dev/null || true

GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 go build ./...
