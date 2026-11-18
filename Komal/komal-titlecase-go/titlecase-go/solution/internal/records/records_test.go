package records

import (
	"bytes"
	"strings"
	"testing"
)

func TestProtocol(t *testing.T) {
	for _, tt := range []struct{ in, want string }{
		{"", ""}, {"\n", "[]\n"}, {"a\n\n", "[a]\n[]\n"}, {"a", "[a]\n"},
		{"a\r\nb\n", "[a]\n[b]\n"}, {" a\t \n", "[ a\t ]\n"},
		{"a\u2028b\n", "[a\u2028b]\n"},
	} {
		var out bytes.Buffer
		if err := Run(strings.NewReader(tt.in), &out, func(s string) string { return "[" + s + "]" }); err != nil {
			t.Fatal(err)
		}
		if out.String() != tt.want {
			t.Fatalf("%q: %q want %q", tt.in, out.String(), tt.want)
		}
	}
	long := strings.Repeat("x", 200000)
	var out bytes.Buffer
	if err := Run(strings.NewReader(long), &out, func(s string) string { return s }); err != nil {
		t.Fatal(err)
	}
	if out.String() != long+"\n" {
		t.Fatal("long record truncated")
	}
}
