# titlecase-go

This Harbor task ports the behavior of the original
[python-titlecase](../python-titlecase) project to a Go command-line program.
The Go implementation uses only the standard library and reads text from
standard input, writing its title-cased lines to standard output.

## Harbor environment

The environment uses `golang:1.23`. Its Compose configuration builds with the
parent `tutorial` directory as context so the sibling `python-titlecase`
directory is available. The Dockerfile copies that source into
`/workspace/repo`, excluding `.git`.

The task solution script is `solution/solve.sh`. Run it in the Harbor
environment to create `go.mod` and the Go source in `/workspace/repo`. The
script also removes Python files from that workspace.

## Verification

The verifier builds the Go program and checks:

- That it builds successfully.
- That no `.py` files remain in the workspace.
- That its output matches the hidden behavior fixtures.

To run the task with Harbor from the parent `tutorial` directory:

```sh
harbor run -p ./titlecase-go -a oracle
```

The public input and expected-output fixtures are in `tests/data/`.
