package main

import (
"bufio"
"bytes"
"context"
"encoding/base64"
"encoding/json"
"fmt"
"io/fs"
"os"
"os/exec"
"path/filepath"
"strings"
"time"
)

type TestCase struct {
Args []string `json:"args"`
Out  string   `json:"out"`
}

type Reward struct {
Reward    float64 `json:"reward"`
Build     float64 `json:"build"`
NoPython  float64 `json:"no_python"`
Behaviour float64 `json:"behaviour"`
}

func hasPythonFiles(root string) bool {
found := false
_ = filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
if err != nil {
return nil
}
if !d.IsDir() && strings.HasSuffix(strings.ToLower(d.Name()), ".py") {
found = true
return filepath.SkipAll
}
return nil
})
return found
}

func runCase(binPath string, args []string) (string, error) {
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
cmd := exec.CommandContext(ctx, binPath, args...)
var stdout bytes.Buffer
cmd.Stdout = &stdout
err := cmd.Run()
return stdout.String(), err
}

func writeReward(r Reward) {
_ = os.MkdirAll("/logs/verifier", 0755)
data, _ := json.MarshalIndent(r, "", "  ")
_ = os.WriteFile("/logs/verifier/reward.json", append(data, '\n'), 0644)
fmt.Printf("Reward written: %s\n", string(data))
}

func main() {
repoDir := "/workspace/repo"
binPath := "/tmp/figlet"

buildScore := 0.0
buildCmd := exec.Command("go", "build", "-o", binPath, ".")
buildCmd.Dir = repoDir
if out, err := buildCmd.CombinedOutput(); err == nil {
buildScore = 1.0
} else {
fmt.Printf("Build failed: %v\n%s\n", err, string(out))
}

behaviourScore := 0.0
matched := 0
total := 0

f, err := os.Open("/tests/data/hidden.jsonl")
if err != nil {
fmt.Printf("Failed to open hidden.jsonl: %v\n", err)
writeReward(Reward{})
fmt.Println("No secret for you. Yet.")
return
}
defer f.Close()

scanner := bufio.NewScanner(f)
scanner.Buffer(make([]byte, 1024*1024), 10*1024*1024)
for scanner.Scan() {
line := strings.TrimSpace(scanner.Text())
if line == "" {
continue
}
var tc TestCase
if err := json.Unmarshal([]byte(line), &tc); err != nil {
continue
}
total++
if buildScore == 1.0 {
got, runErr := runCase(binPath, tc.Args)
if runErr == nil && got == tc.Out {
matched++
}
}
}

if total > 0 && buildScore == 1.0 {
behaviourScore = float64(matched) / float64(total)
}

noPythonScore := 0.0
if buildScore == 1.0 && !hasPythonFiles(repoDir) && matched >= 1 {
noPythonScore = 1.0
}

totalReward := (1.0*buildScore + 1.0*noPythonScore + 4.0*behaviourScore) / 6.0
writeReward(Reward{
Reward:    totalReward,
Build:     buildScore,
NoPython:  noPythonScore,
Behaviour: behaviourScore,
})

fmt.Printf("Matched %d / %d hidden cases (behaviour=%.6f)\n", matched, total, behaviourScore)

if behaviourScore == 1.0 && matched == total && total > 0 {
b64Bytes, err := os.ReadFile("/tests/secret.b64")
if err == nil {
decoded, decErr := base64.StdEncoding.DecodeString(strings.TrimSpace(string(b64Bytes)))
if decErr == nil {
bannerOut, runErr := runCase(binPath, []string{"-f", "slant", string(decoded)})
if runErr == nil {
fmt.Println("*** SECRET UNLOCKED ***")
fmt.Print(bannerOut)
return
}
}
}
}
fmt.Println("No secret for you. Yet.")
}
