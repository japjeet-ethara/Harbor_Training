package main

import (
	"encoding/json"
	"os/exec"
	"testing"
)

func TestPythonSuite(t *testing.T) {
	py := `
import json, sys
sys.path.insert(0, r"C:\Users\PriyeshSingh\Projects\python-titlecase")
from titlecase import titlecase
from titlecase.tests import TEST_DATA
rows = []
for src, _ in TEST_DATA:
    if "\n" in src or "\r" in src:
        continue
    rows.append({"in": src, "out": titlecase(src)})
json.dump(rows, sys.stdout)
`
	cmd := exec.Command(`C:\Users\PriyeshSingh\AppData\Local\Programs\Python\Python312\python.exe`, "-c", py)
	out, err := cmd.Output()
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			t.Fatalf("%v\n%s", err, ee.Stderr)
		}
		t.Fatal(err)
	}
	var rows []struct {
		In  string `json:"in"`
		Out string `json:"out"`
	}
	if err := json.Unmarshal(out, &rows); err != nil {
		t.Fatal(err)
	}
	for _, row := range rows {
		got := TitleCase(row.In)
		if got != row.Out {
			t.Errorf("input %q\n got %q\nwant %q", row.In, got, row.Out)
		}
	}
	if len(rows) < 40 {
		t.Fatalf("only compared %d cases", len(rows))
	}
}
