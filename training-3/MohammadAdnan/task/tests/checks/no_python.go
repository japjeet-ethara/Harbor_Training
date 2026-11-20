package main

import (
	"bytes"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// Strings that only appear in Python titlecase source or in a Python interpreter.
// They catch the original code renamed to another extension, embedded in the Go binary, or a
// bundled interpreter. Checked in every repo file and in the built binary.
var pythonMarkers = [][]byte{
	[]byte("def titlecase("),
	[]byte("import regex"),
	[]byte("SMALL_FIRST = "),
	[]byte("Py_Initialize"),
	[]byte("PyRun_SimpleString"),
}

func hasMarker(data []byte) []byte {
	for _, m := range pythonMarkers {
		if bytes.Contains(data, m) {
			return m
		}
	}
	return nil
}

// containsPython reports a .py file anywhere under the repo, Python source under any other name,
// or Python embedded in the built program.
func containsPython() bool {
	found := false
	_ = filepath.WalkDir(repo, func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if strings.HasSuffix(p, ".py") {
			fmt.Println("no_python: .py file", p)
			found = true
			return nil
		}
		if info, err := d.Info(); err == nil && info.Size() < 200<<20 {
			if data, err := os.ReadFile(p); err == nil {
				if m := hasMarker(data); m != nil {
					fmt.Printf("no_python: Python code (%q) in %s\n", m, p)
					found = true
				}
			}
		}
		return nil
	})
	if data, err := os.ReadFile(binary); err == nil {
		if m := hasMarker(data); m != nil {
			fmt.Printf("no_python: Python code (%q) inside the built program\n", m)
			found = true
		}
	}
	return found
}
