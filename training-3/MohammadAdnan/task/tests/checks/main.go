// Grader for the titlecase-go Harbor task. Go standard library only; runs with no Python present.
//
//	build      (weight 1): build.go
//	no_python  (weight 1): no_python.go — needs build AND no Python AND behaviour > 0
//	behaviour  (weight 4): behaviour.go — (accuracy - 0.5) / 0.5 on the hidden answers, min 0
//
// The agent's program runs as the unprivileged user "nobody" from an empty folder, after /tests and
// /logs are locked to root, so it cannot read the answers (cheat "read the exam").
package main

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

const (
	repo       = "/workspace/repo"
	binary     = "/tmp/titlecase-under-test"
	dataDir    = "/tests/data"
	rewardPath = "/logs/verifier/reward.json"
)

// lockDown makes /tests and /logs readable by root only (the grader), not by the program under test.
func lockDown() {
	if os.Geteuid() != 0 {
		fmt.Println("warning: grader is not root; cannot lock /tests")
		return
	}
	for _, root := range []string{"/tests", "/logs"} {
		_ = filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
			if err == nil {
				_ = os.Chown(p, 0, 0)
				if d.IsDir() {
					_ = os.Chmod(p, 0o700)
				} else {
					_ = os.Chmod(p, 0o600)
				}
			}
			return nil
		})
	}
}

func main() {
	lockDown()
	_ = os.MkdirAll(filepath.Dir(rewardPath), 0o700)

	build := 0.0
	if checkBuild() {
		build = 1
	}

	python := false
	if build == 1 {
		python = containsPython()
	}

	// accuracy = share of the 100,000 hidden answers matched exactly. Partial credit starts above
	// 50%: behaviour = (accuracy - 0.5) / 0.5, clamped to [0, 1]. An echo program already matches
	// ~1.5% (titles that are correct as typed) and a port of only the easy rules ~17%; neither earns
	// anything. no_python is paid only when behaviour > 0, i.e. when the port really works.
	accuracy := 0.0
	if build == 1 && !python {
		accuracy, _ = checkBehaviour()
	}
	beh := (accuracy - 0.5) / 0.5
	if beh < 0 {
		beh = 0
	}

	noPython := 0.0
	if build == 1 && !python && beh > 0 {
		noPython = 1
	}

	reward := (1*build + 1*noPython + 4*beh) / 6
	result := map[string]float64{"reward": reward, "build": build, "no_python": noPython,
		"behaviour": beh, "accuracy": accuracy}
	data, _ := json.Marshal(result)
	if err := os.WriteFile(rewardPath, data, 0o644); err != nil {
		fmt.Println("cannot write reward:", err)
		os.Exit(1)
	}
	fmt.Println(string(data))
}
