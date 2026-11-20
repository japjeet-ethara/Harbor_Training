#!/bin/bash
set -euo pipefail

reward=/logs/verifier/reward.txt
mkdir -p /logs/verifier
printf '0\n' > "$reward"

reject() {
  printf '%s\n' "$1" >&2
  exit 0
}

cd /workspace/repo || reject 'Missing submission workspace'
invalid=$(find . ! -type d ! -type f -print -quit) ||
  reject 'Cannot inspect submission workspace'
[[ -z "$invalid" ]] || reject 'Submission contains a link or special file'
python=$(find . -type f -iname '*.py' -print -quit) ||
  reject 'Cannot inspect submission source'
[[ -z "$python" ]] || reject 'Submission contains Python source'
[[ -f go.mod && ! -e vendor ]] || reject 'Expected a Go module without vendored dependencies'

scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
mkdir -m 0755 "$scratch/jail"

# Build source with a fixed toolchain, without network dependencies or C tooling.
go_local() {
  env -i PATH=/usr/local/go/bin:/usr/bin:/bin HOME="$scratch" \
    GOCACHE="$scratch/gocache" GOPATH="$scratch/gopath" GOTOOLCHAIN=local \
    GOENV=off GOWORK=off GOPROXY=off GOSUMDB=off CGO_ENABLED=0 \
    GOFLAGS=-mod=readonly go "$@"
}

dependency_format='{{if not .Standard}}{{if .Module}}{{if not .Module.Main}}{{.ImportPath}}{{end}}{{else}}{{.ImportPath}}{{end}}{{end}}'
go_local list -deps -f "$dependency_format" ./... > "$scratch/dependencies" ||
  reject 'Could not resolve the Go packages'
if grep -q '[^[:space:]]' "$scratch/dependencies"; then
  reject 'Submission uses a non-standard-library dependency'
fi

[[ "$(go_local list -f '{{.Name}}' .)" == main ]] ||
  reject 'The root package is not a Go executable'
go_local build -o "$scratch/build/" ./... || reject 'go build ./... failed'
go_local build -o "$scratch/submission" . || reject 'Could not build the submission executable'
install -m 0555 "$scratch/submission" "$scratch/jail/titlecase"

# Canonicalize fixture line endings before passing inputs or comparing answers.
sed 's/\r$//' /tests/data/inputs.txt > "$scratch/inputs"
sed 's/\r$//' /tests/data/answers.txt > "$scratch/expected"
total=$(wc -l < "$scratch/expected")
if (( total == 0 || total != $(wc -l < "$scratch/inputs") )); then
  reject 'Invalid verifier fixtures'
fi

# The submission gets a read-only executable, an empty environment, stdin, and
# stdout. The jail contains no shell, interpreter, /proc, or grading files.
chroot_path=$(command -v chroot) || reject 'Verifier sandbox is unavailable'
cd "$scratch"
if ! (
  ulimit -f 16384
  exec timeout --kill-after=5s 90s env -i \
    "$chroot_path" --userspec=65534:65534 --groups=65534 "$scratch/jail" /titlecase
) < "$scratch/inputs" > "$scratch/actual" 2>/dev/null; then
  reject 'Submission exited unsuccessfully or exceeded a verifier limit'
fi

if (( $(wc -l < "$scratch/actual") != total )); then
  reject 'Expected exactly one output line per input line'
fi
last_byte=$(tail -c 1 "$scratch/actual" | od -An -tu1 | tr -d '[:space:]')
[[ "$last_byte" == 10 ]] || reject 'Output must end with a newline'

# Force string comparison, including for titles that look like numbers.
LC_ALL=C awk '
  FILENAME == ARGV[1] { want[FNR] = $0; total++; next }
  ("x" $0) == ("x" want[FNR]) { matched++ }
  END {
    printf "%d/%d hidden lines matched\n", matched, total > "/dev/stderr"
    # Preserve low partial scores, but reserve passing credit for exact parity.
    fraction = matched / total
    reward = matched == total ? 1 : (fraction > 0.19 ? 0.19 : fraction)
    printf "%.6f\n", reward
  }
' "$scratch/expected" "$scratch/actual" > "$scratch/score"
cat "$scratch/score" > "$reward"
