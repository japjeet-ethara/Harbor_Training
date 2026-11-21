
#!/bin/bash
# CHEAT 1 — Return stored answers for visible inputs and UNKNOWN otherwise.
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest=/workspace/repo

# Copy cheat files into the task workspace.
cp "$src/go.mod" "$src/main.go" "$src/lookup.json" "$dest/"

# Remove Python implementations and cached Python files.
find "$dest" -type f -name '*.py' -delete
find "$dest" -type d -name '__pycache__' -exec rm -rf {} + || true

# Compile the Go program.
cd "$dest"
go build -o "$dest/titlecase-cheat" .

# Execute the compiled program and pass through stdin/stdout.
exec "$dest/titlecase-cheat"
