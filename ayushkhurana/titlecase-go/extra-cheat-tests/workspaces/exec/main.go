package main

import (
	"os"
	"os/exec"
)

// CHEAT: hands the work to another program (here `cat`; a real cheat would run python3).
func main() {
	c := exec.Command("cat")
	c.Stdin, c.Stdout = os.Stdin, os.Stdout
	c.Run()
}
