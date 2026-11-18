package format

import (
	"encoding/json"
	"os"
	"testing"
)

func TestPatternsAgainstPython(t *testing.T) {
	data, err := os.ReadFile("testdata/patterns.json")
	if err != nil {
		t.Fatal(err)
	}
	var rows []struct {
		Name, Mode, Input string
		Found             bool
		Start, End        int
		Groups            []string
	}
	if err := json.Unmarshal(data, &rows); err != nil {
		t.Fatal(err)
	}
	for _, r := range rows {
		p := patterns[r.Name]
		m, ok := p.Match(r.Input)
		if r.Mode == "search" {
			m, ok = p.Search(r.Input)
		}
		if ok != r.Found {
			t.Fatalf("%s %s %q: found %v want %v", r.Name, r.Mode, r.Input, ok, r.Found)
		}
		if !ok {
			continue
		}
		if m.Start() != r.Start || m.End() != r.End {
			t.Fatalf("%s %s %q: span %d:%d want %d:%d", r.Name, r.Mode, r.Input, m.Start(), m.End(), r.Start, r.End)
		}
		for i, want := range r.Groups {
			if got := m.Group(i); got != want {
				t.Fatalf("%s %q group %d: %q want %q", r.Name, r.Input, i, got, want)
			}
		}
	}
	t.Logf("%d direct Python fixtures passed", len(rows))
}
