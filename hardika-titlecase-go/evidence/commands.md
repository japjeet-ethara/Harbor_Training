# Recorded commands

The Windows checks used CPython 3.12.14 from the Codex desktop runtime, regex 2026.11.15 from PyPI, Harbor 0.26.0 and the verified Go 1.23.12 Windows archive. The following PowerShell commands are expressed relative to the working directory used during validation. `$py`, `$go` and `$harbor` denote the absolute executable paths in the isolated work directory or bundled runtime.

```powershell
$p = "$PWD/work/hardika-titlecase-go"
$app = "$PWD/work/titlecase.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:GOTOOLCHAIN = 'local'
$env:GOCACHE = "$PWD/work/go123-cache"

& $py -VV
& $go version
& $py "$p/tests/gen.py"
& $py "$p/tests/gen.py" --output "$PWD/work/dataset-regeneration"
Push-Location "$p/solution/go"
& $go build ./...
& $go build -o $app .
Pop-Location
& $py "$p/tools/verify_reference.py" $app
& $py "$p/tools/stress.py" $app
& $py "$p/tools/check_protocol.py" $app
& $py "$p/tools/check_grader.py" $go
& $py "$p/tools/unicode_tables.py" --output "$PWD/work/unicode-regenerated-release.go"
& $harbor lint --select ALL --json $p
docker version
docker build --tag titlecase-go-agent:section18 "$p/environment"
& $harbor run -p $p --env docker -a oracle --jobs-dir "$PWD/work/windows-harbor-jobs" --job-name oracle
```

The byte comparison that confirmed regeneration is recorded in `reproducibility.log`. The original source was downloaded from GitHub’s commit archive endpoint. The Go archive matched SHA-256 `07c35866cdd864b81bb6f1cfbf25ac7f87ddc3a976ede1bf5112acbb12dfe6dc` from Go’s download metadata.

To repeat the independent checks on Linux, use `bash tools/validate.sh`. To build the shipped images and launch the three Harbor jobs, use `bash tools/run_harbor.sh`.
