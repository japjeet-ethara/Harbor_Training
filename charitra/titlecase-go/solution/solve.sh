#!/usr/bin/env bash
set -euo pipefail

# Harbor mounts this directory at /solution. Resolve relative paths so the
# same script also works from an extracted task during local verification.
solution_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="/workspace/repo"

test -d "$repo_dir"
test -f "$repo_dir/LICENSE.txt"
cp "$solution_dir/go.mod" "$repo_dir/go.mod"
cp "$solution_dir/main.go" "$repo_dir/main.go"
cp "$solution_dir/unicode_tables.go" "$repo_dir/unicode_tables.go"
cp "$solution_dir/UNICODE-LICENSE.txt" "$repo_dir/UNICODE-LICENSE.txt"

# Only the candidate repository is changed; authoring tools and graders
# elsewhere are intentionally untouched.
find "$repo_dir" -type f \( -name '*.py' -o -name '*.pyc' \) -delete
find "$repo_dir" -depth -type d -name '__pycache__' -exec rmdir {} + 2>/dev/null || true
cd "$repo_dir"
GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off CGO_ENABLED=0 go build ./...
