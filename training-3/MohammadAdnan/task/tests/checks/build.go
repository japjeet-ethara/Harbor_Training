package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func goCmd(args ...string) error {
	cmd := exec.Command("go", args...)
	cmd.Dir = repo
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stdout
	return cmd.Run()
}

// checkBuild: `go build ./...` and `go build -o <bin> .` pass in /workspace/repo,
// and go.mod has no require lines (Go standard library only).
func checkBuild() bool {
	_ = os.Remove(binary)
	// Build every package, but write any executables to a temporary folder: a plain
	// `go build ./...` writes the binary into the repo under the module name, which fails for a
	// correct port if a folder with that name (e.g. the old titlecase/ package dir) is left behind.
	outDir, err := os.MkdirTemp("", "buildall")
	if err != nil {
		return false
	}
	defer os.RemoveAll(outDir)
	if err := goCmd("build", "-buildvcs=false", "-o", outDir+string(os.PathSeparator), "./..."); err != nil {
		fmt.Println("build: go build ./... failed:", err)
		return false
	}
	if err := goCmd("build", "-buildvcs=false", "-o", binary, "."); err != nil {
		fmt.Println("build: go build -o <bin> . failed:", err)
		return false
	}
	mod, err := os.ReadFile(filepath.Join(repo, "go.mod"))
	if err != nil {
		fmt.Println("build: no go.mod")
		return false
	}
	for _, line := range strings.Split(string(mod), "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), "require") {
			fmt.Println("build: go.mod has a require line (standard library only)")
			return false
		}
	}
	_ = os.Chmod(binary, 0o755)
	fmt.Println("build: ok")
	return true
}
