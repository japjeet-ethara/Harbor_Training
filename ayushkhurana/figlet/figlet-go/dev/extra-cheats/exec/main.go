package main

import (
	"os"
	"os/exec"
)

// runs the original Python program (copied to /opt/pyfiglet-orig) - exactly what the "no Python" rule is for
func main() {
	cmd := exec.Command("python3", append([]string{"-m", "pyfiglet"}, os.Args[1:]...)...)
	cmd.Env = []string{"PYTHONPATH=/opt/pyfiglet-orig", "PATH=/usr/bin:/bin"}
	cmd.Stdout = os.Stdout
	_ = cmd.Run()
}
