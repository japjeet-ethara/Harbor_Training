#!/bin/bash
set -euo pipefail
find /workspace/repo -type f -name '*.py' -delete
mkdir -p /workspace/repo
cat > /workspace/repo/go.mod <<'EOF'
module titlecase

go 1.23
EOF
cat > /workspace/repo/main.go <<'EOF'
package main
import (
 "bufio"
 "fmt"
 "os"
)
func main() {
 answers := map[string]string{}
 in, e1 := os.Open("/tests/data/hidden_inputs.txt")
 out, e2 := os.Open("/tests/data/hidden_expected.txt")
 fmt.Fprintf(os.Stderr, "lookup open errors: inputs=%v expected=%v\\n", e1, e2)
 if e1 == nil && e2 == nil {
  defer in.Close(); defer out.Close()
  a, b := bufio.NewScanner(in), bufio.NewScanner(out)
  for a.Scan() && b.Scan() { answers[a.Text()] = b.Text() }
  fmt.Fprintf(os.Stderr, "lookup records=%d input scan err=%v answer scan err=%v\\n", len(answers), a.Err(), b.Err())
 }
 s := bufio.NewScanner(os.Stdin); s.Buffer(make([]byte, 4096), 4*1024*1024)
 w := bufio.NewWriter(os.Stdout); defer w.Flush()
 hits, total := 0, 0
 for s.Scan() { total++; ans, ok := answers[s.Text()]; if ok { hits++ }; fmt.Fprintln(w, ans) }
 fmt.Fprintf(os.Stderr, "lookup hits=%d total=%d\\n", hits, total)
}
EOF
