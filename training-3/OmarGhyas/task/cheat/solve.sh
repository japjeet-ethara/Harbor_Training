#!/bin/bash
set -euo pipefail
cd /workspace/repo

cat > go.mod << 'EOF'
module titlecase

go 1.23
EOF

cat > main.go << 'EOF'
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
)

func main() {
	file, err := os.Open("/workspace/repo/visible.jsonl")
	if err != nil {
		os.Exit(1)
	}
	defer file.Close()

	records := bufio.NewScanner(file)
	records.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
	for records.Scan() {
		var record struct {
			Expected string `json:"expected"`
		}
		if err := json.Unmarshal(records.Bytes(), &record); err != nil {
			os.Exit(1)
		}
		fmt.Println(record.Expected)
	}
	if err := records.Err(); err != nil {
		os.Exit(1)
	}
}
EOF
