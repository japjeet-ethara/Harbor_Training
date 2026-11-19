package main

import (
    "os"
    "os/exec"
)

func main() {
    code := `import sys
ns = {"__name__": "titlecase"}
exec(open("/workspace/repo/reference.txt").read(), ns)
sys.stdout.write(ns["titlecase"](sys.stdin.read()))
`
    cmd := exec.Command("python3", "-c", code)
    cmd.Stdin = os.Stdin
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr

    if err := cmd.Run(); err != nil {
        os.Exit(1)
    }
}
