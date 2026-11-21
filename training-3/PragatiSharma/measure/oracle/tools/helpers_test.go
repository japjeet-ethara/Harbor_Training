package main

// Test harness for the casing helpers. It is copied next to the built sources in
// a throwaway container and is not part of the solution.
//
// CASING_REF:   per-code-point reference from mkcasing.py
// HELPER_CASES: string cases from mkhelpercases.py

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"testing"
	"unicode"
)

func parseSeq(t *testing.T, s string) string {
	var b strings.Builder
	for _, h := range strings.Fields(s) {
		v, err := strconv.ParseUint(h, 16, 32)
		if err != nil {
			t.Fatalf("bad hex %q", h)
		}
		b.WriteRune(rune(v))
	}
	return b.String()
}

func codePoints(s string) string {
	parts := []string{}
	for _, r := range s {
		parts = append(parts, fmt.Sprintf("U+%04X", r))
	}
	return "[" + strings.Join(parts, " ") + "]"
}

func readRows(t *testing.T, env string) [][]string {
	f, err := os.Open(os.Getenv(env))
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	var rows [][]string
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if strings.HasPrefix(line, "#") {
			t.Log(line)
			continue
		}
		rows = append(rows, strings.Split(line, "\t"))
	}
	if err := sc.Err(); err != nil {
		t.Fatal(err)
	}
	return rows
}

func TestEveryCodePoint(t *testing.T) {
	type want struct {
		upper, lower, capitalize string
		class                    uint8
	}
	ref := map[rune]want{}
	for _, f := range readRows(t, "CASING_REF") {
		cp, _ := strconv.ParseUint(f[0], 16, 32)
		k, _ := strconv.Atoi(f[4])
		ref[rune(cp)] = want{parseSeq(t, f[1]), parseSeq(t, f[2]), parseSeq(t, f[3]), uint8(k)}
	}
	checked, bad := 0, 0
	report := func(what string, r rune, got, exp string) {
		bad++
		if bad <= 30 {
			t.Errorf("%s(%U): got %s want %s", what, r, codePoints(got), codePoints(exp))
		}
	}
	for r := rune(0); r <= unicode.MaxRune; r++ {
		if r >= 0xD800 && r <= 0xDFFF {
			continue
		}
		s := string(r)
		w, ok := ref[r]
		if !ok {
			w = want{s, s, s, caseOther}
		}
		checked++
		if got := pyUpper(s); got != w.upper {
			report("pyUpper", r, got, w.upper)
		}
		if got := pyLower(s); got != w.lower {
			report("pyLower", r, got, w.lower)
		}
		if got := pyCapitalize(s); got != w.capitalize {
			report("pyCapitalize", r, got, w.capitalize)
		}
		if got := sigmaClass(r); got != w.class {
			report("sigmaClass", r, fmt.Sprint(got), fmt.Sprint(w.class))
		}
	}
	t.Logf("code points checked %d (4 properties each, %d reference rows), mismatches %d", checked, len(ref), bad)
}

// TestRegexClasses checks \w, \s and re.IGNORECASE folding for every code point
// against CLASSES_REF from mkclasses.py (measured with Python's re module).
// It is skipped when CLASSES_REF is not set (the round-1 casing-only build).
func TestRegexClasses(t *testing.T) {
	if os.Getenv("CLASSES_REF") == "" {
		t.Skip("CLASSES_REF not set")
	}
	type want struct {
		word, space bool
		fold        rune // 0: matches no ASCII letter
	}
	ref := map[rune]want{}
	for _, f := range readRows(t, "CLASSES_REF") {
		cp, _ := strconv.ParseUint(f[0], 16, 32)
		w := want{word: f[1] == "1", space: f[2] == "1"}
		if f[3] != "-" {
			w.fold = rune(f[3][0])
		}
		ref[rune(cp)] = w
	}
	checked, bad := 0, 0
	for r := rune(0); r <= unicode.MaxRune; r++ {
		if r >= 0xD800 && r <= 0xDFFF {
			continue
		}
		checked++
		w := ref[r]
		if got := isPyWord(r); got != w.word {
			bad++
			t.Errorf("isPyWord(%U) = %v, want %v", r, got, w.word)
		}
		if got := isPySpace(r); got != w.space {
			bad++
			t.Errorf("isPySpace(%U) = %v, want %v", r, got, w.space)
		}
		f := reFold(r)
		isLetter := f >= 'a' && f <= 'z'
		if (w.fold == 0 && isLetter) || (w.fold != 0 && f != w.fold) {
			bad++
			t.Errorf("reFold(%U) = %U, want %q", r, f, w.fold)
		}
		if bad > 30 {
			t.Fatal("too many mismatches")
		}
	}
	t.Logf("code points checked %d (\\w, \\s, IGNORECASE fold; %d reference rows), mismatches %d", checked, len(ref), bad)
}

func TestStringCases(t *testing.T) {
	rows := readRows(t, "HELPER_CASES")
	bad := 0
	for _, f := range rows {
		in := parseSeq(t, f[0])
		for i, fn := range []struct {
			name string
			f    func(string) string
		}{{"pyUpper", pyUpper}, {"pyLower", pyLower}, {"pyCapitalize", pyCapitalize}} {
			exp := parseSeq(t, f[i+1])
			if got := fn.f(in); got != exp {
				bad++
				if bad <= 30 {
					t.Errorf("%s(%s): got %s want %s", fn.name, codePoints(in), codePoints(got), codePoints(exp))
				}
			}
		}
	}
	t.Logf("string cases %d (x3 functions), mismatches %d", len(rows), bad)
}
