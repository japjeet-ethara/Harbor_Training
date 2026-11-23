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
