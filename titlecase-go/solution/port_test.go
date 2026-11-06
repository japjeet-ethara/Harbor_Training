package main

import (
	"os"
	"os/exec"
	"strings"
	"testing"
)

func TestPythonSuite(t *testing.T) {
	script := `
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"../environment/python-titlecase").resolve()))
from titlecase import titlecase
from titlecase.tests import TEST_DATA

def emit(text):
    data = text.encode("utf-8")
    sys.stdout.buffer.write(len(data).to_bytes(4, "little"))
    sys.stdout.buffer.write(data)

for src, _ in TEST_DATA:
    emit(src)
    emit(titlecase(src))

root = Path("..") / "tests" / "data"
for name in ("inputs.txt", "hidden_inputs.txt"):
    for line in (root / name).read_text(encoding="utf-8").splitlines():
        emit(line)
        emit(titlecase(line))
`
	cmd := exec.Command("python", "-c", script)
	cmd.Dir = "."
	out, err := cmd.Output()
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			t.Fatalf("python: %v\n%s", err, ee.Stderr)
		}
		t.Fatal(err)
	}
	i := 0
	next := func() string {
		t.Helper()
		if i+4 > len(out) {
			t.Fatal("truncated case stream")
		}
		n := int(out[i]) | int(out[i+1])<<8 | int(out[i+2])<<16 | int(out[i+3])<<24
		i += 4
		if i+n > len(out) {
			t.Fatal("truncated case bytes")
		}
		s := string(out[i : i+n])
		i += n
		return s
	}
	mismatches := 0
	for i < len(out) {
		src := next()
		want := next()
		got := titlecase(src, true)
		if got != want {
			mismatches++
			if mismatches <= 12 {
				t.Errorf("mismatch\n in: %q\nwant: %q\n got: %q", src, want, got)
			}
		}
	}
	if mismatches > 0 {
		t.Fatalf("%d mismatches", mismatches)
	}
}

func TestStdinLines(t *testing.T) {
	raw, err := os.ReadFile("../tests/data/hidden_inputs.txt")
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command("go", "run", ".")
	cmd.Stdin = strings.NewReader(string(raw))
	out, err := cmd.Output()
	if err != nil {
		t.Fatal(err)
	}
	lines := strings.Split(strings.TrimRight(string(raw), "\n"), "\n")
	got := strings.Split(strings.TrimRight(string(out), "\n"), "\n")
	if len(got) != len(lines) {
		t.Fatalf("line count %d != %d", len(got), len(lines))
	}
}
