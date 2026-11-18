"""Check 1 - build (weight 1): `go build ./...` passes in the agent's repo.

The binaries are written into a throw-away directory (`-o dir/`). Without that,
a module that happens to be called like a leftover directory (e.g. module
`titlecase` next to the old `titlecase/` package folder) makes `go build` fail
on a file-name clash even though the code is fine.
"""
import rewardkit as rk

rk.command_succeeds(
    'd="$(mktemp -d)"; go build -o "$d/" ./...; rc=$?; rm -rf "$d"; exit $rc',
    timeout=300,
    name="go_build",
)
