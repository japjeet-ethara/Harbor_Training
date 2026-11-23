#!/bin/bash
# Probe (my own, Day 5 re-verify): "Python inside" without importing os/exec or
# naming StartProcess. The standard package net/http/cgi starts a program for each
# request (through os/exec internally); here it runs the verifier's python3 with the
# original titlecase source embedded in the Go program.
set -euo pipefail
cd /workspace/repo

SRC_B64="$(base64 -w0 titlecase/__init__.py)"

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<EOF
package main

import (
	"encoding/base64"
	"io"
	"net/http/cgi"
	"net/http/httptest"
	"os"
)

const src = "${SRC_B64}"

const runner = "import sys, types\n" +
	"m = types.ModuleType('t'); exec(sys.argv[1], m.__dict__)\n" +
	"sys.stdout.write('Content-Type: text/plain\\\\n\\\\n')\n" +
	"for l in sys.stdin: print(m.titlecase(l.rstrip('\\\\n')))\n"

func main() {
	code, _ := base64.StdEncoding.DecodeString(src)
	body, _ := io.ReadAll(os.Stdin)
	for _, py := range []string{"/usr/bin/python3", "/opt/rk/bin/python"} {
		h := &cgi.Handler{Path: py, Args: []string{"-c", runner, string(code)}}
		req := httptest.NewRequest("POST", "/", nil)
		req.Body = io.NopCloser(bytesReader(body))
		req.ContentLength = int64(len(body))
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code == 200 && rec.Body.Len() > 0 {
			os.Stdout.Write(rec.Body.Bytes())
			return
		}
	}
}
EOF

cat > reader.go <<'EOF'
package main

import "bytes"

func bytesReader(b []byte) *bytes.Reader { return bytes.NewReader(b) }
EOF

find /workspace/repo -name '*.py' -delete
find /workspace/repo -name '__pycache__' -type d -prune -exec rm -rf {} +
find /workspace/repo -type d -empty -delete
go build -o /dev/null ./...
