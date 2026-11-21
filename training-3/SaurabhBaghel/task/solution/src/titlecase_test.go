package main

import "testing"

func TestSubphraseOnlyCapitalizesLowercaseSmallWords(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"ocean U.S. EN time input/output 2^10 or", "Ocean U.S. EN Time Input/Output 2^10 Or"},
		{"history: BUT game house", "History: BUT Game House"},
		{"history: but game house", "History: But Game House"},
	}
	for _, test := range tests {
		if got := TitleCase(test.input); got != test.want {
			t.Errorf("TitleCase(%q) = %q, want %q", test.input, got, test.want)
		}
	}
}

func TestPythonCaseExpansion(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"ﬁnal", "FInal"},
		{"ﬂight", "FLight"},
		{"İZMIR", "I\u0307zmir"},
		{"ßeta", "SSeta"},
	}
	for _, test := range tests {
		if got := TitleCase(test.input); got != test.want {
			t.Errorf("TitleCase(%q) = %q, want %q", test.input, got, test.want)
		}
	}
}
