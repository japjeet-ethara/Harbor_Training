package pattern

import "testing"

func TestInterpreter(t *testing.T) {
	tests := []struct {
		name        string
		node        Node
		input, want string
		start, end  int
	}{
		{"ordered", Alt(Text("a"), Text("an")), "and", "a", 0, 1},
		{"backtrack", Seq(Alt(Text("a"), Text("ab")), Text("c")), "abc", "abc", 0, 3},
		{"greedy", Rep(Chars("a"), 1, -1, false), "aaaa!", "aaaa", 0, 4},
		{"lazy", Rep(Chars("a"), 1, -1, true), "aaaa!", "a", 0, 1},
		{"greedy suffix", Seq(Rep(Chars("a"), 1, -1, false), Text("ab")), "aaaab", "aaaab", 0, 5},
		{"unicode span", Seq(Assert(Boundary), Text("é!")), " é!", "é!", 1, 3},
		{"dollar", Seq(Text("a"), Assert(End)), "a\n", "a", 0, 1},
		{"fold", CI(Text("isk")), "İſK", "İſK", 0, 3},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m, ok := Compile(tt.node).Search(tt.input)
			if !ok || m.Group(0) != tt.want || m.Start() != tt.start || m.End() != tt.end {
				t.Fatalf("got %+v %v", m, ok)
			}
		})
	}
	if _, ok := Compile(Seq(Text("a"), Assert(StrictEnd))).Search("a\n"); ok {
		t.Fatal("strict end accepted final newline")
	}
}

func TestCaptureRestorationAndReplacement(t *testing.T) {
	p := Compile(Seq(Alt(Seq(Cap(1, Text("a")), Text("z")), Cap(2, Text("ab"))), Text("c")))
	m, ok := p.Match("abc")
	if !ok || m.Group(1) != "" || m.Group(2) != "ab" {
		t.Fatalf("capture leak: %+v", m)
	}
	p = Compile(Alt(Text("aba"), Text("ab")))
	if got := p.Replace("ababa ab", func(m Match) string { return "[" + m.Group(0) + "]" }); got != "[aba]ba [ab]" {
		t.Fatal(got)
	}
}

func TestRejectNullableLoop(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("accepted unbounded nullable loop")
		}
	}()
	Compile(Rep(Text(""), 0, -1, false))
}
