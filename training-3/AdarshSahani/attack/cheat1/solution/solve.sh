
#!/bin/bash
set -euo pipefail

cd /workspace/repo

cat > go.mod <<'EOF'
module titlecase

go 1.23
EOF

cat > main.go <<'EOF'
package main

import (
	"io"
	"os"
)

func main() {
	_, _ = io.Copy(os.Stdout, os.Stdin)
}
EOF

# Remove Python files from the repository.
find /workspace/repo -type f -name '*.py' -delete

# Verify compilation.
go build ./...
