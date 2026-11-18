package format

import (
	"encoding/json"
	"os"
	"testing"
)

func TestRulePrecedence(t *testing.T) {
	data, err := os.ReadFile("testdata/examples.json")
	if err != nil {
		t.Fatal(err)
	}
	var examples []struct{ Input, Expected string }
	if err := json.Unmarshal(data, &examples); err != nil {
		t.Fatal(err)
	}
	for _, e := range examples {
		if got := Titlecase(e.Input); got != e.Expected {
			t.Errorf("%q: got %q want %q", e.Input, got, e.Expected)
		}
	}
	t.Logf("%d checked reference examples", len(examples))
}
