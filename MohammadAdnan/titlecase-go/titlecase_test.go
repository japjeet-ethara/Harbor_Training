package main

import (
	"strings"
	"testing"
)

func TestStandardCases(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", ""},
		{"word/word", "Word/Word"},
		{"a title and/or string", "A Title and/or String"},
		{"dance with me/let’s face the music and dance", "Dance With Me/Let’s Face the Music and Dance"},
		{"a-b end-to-end two-not-three/three-by-four/five-and", "A-B End-to-End Two-Not-Three/Three-by-Four/Five-And"},
		{"34th 3rd 2nd", "34th 3rd 2nd"},
		{"Q&A with steve jobs: 'that's what happens in technology'", "Q&A With Steve Jobs: 'That's What Happens in Technology'"},
		{"What is AT&T's problem?", "What Is AT&T's Problem?"},
		{"Apple deal with AT&T falls through", "Apple Deal With AT&T Falls Through"},
		{"Words with all consonants like cnn are acronyms", "Words With All Consonants Like CNN Are Acronyms"},
		{"this v that", "This v That"},
		{"this v. that", "This v. That"},
		{"this vs that", "This vs That"},
		{"this vs. that", "This vs. That"},
		{"The SEC's Apple probe: what you need to know", "The SEC's Apple Probe: What You Need to Know"},
		{"'by the Way, small word at the start but within quotes.'", "'By the Way, Small Word at the Start but Within Quotes.'"},
		{"Small word at end is nothing to be afraid of", "Small Word at End Is Nothing to Be Afraid Of"},
		{"Starting Sub-Phrase With a Small Word: a Trick, Perhaps?", "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"},
		{"Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'", "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"},
		{`sub-phrase with a small word in quotes: "a trick, perhaps?"`, `Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"`},
		{"Starting a Hyphen Delimited Sub-Phrase With a Small Word - a Trick, Perhaps?", "Starting a Hyphen Delimited Sub-Phrase With a Small Word - A Trick, Perhaps?"},
		{"Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'a Trick, Perhaps?'", "Hyphen Delimited Sub-Phrase With a Small Word in Quotes - 'A Trick, Perhaps?'"},
		{`Hyphen Delimited sub-phrase with a small word in quotes - "a trick, perhaps?"`, `Hyphen Delimited Sub-Phrase With a Small Word in Quotes - "A Trick, Perhaps?"`},
		{"Snakes on a Plane - The TV Edit - The Famous Line", "Snakes on a Plane - The TV Edit - The Famous Line"},
		{"Starting an Em Dash Delimited Sub-Phrase With a Small Word — a Trick, Perhaps?", "Starting an Em Dash Delimited Sub-Phrase With a Small Word — A Trick, Perhaps?"},
		{"Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'a Trick, Perhaps?'", "Em Dash Delimited Sub-Phrase With a Small Word in Quotes — 'A Trick, Perhaps?'"},
		{`Em Dash Delimited sub-phrase with a small word in quotes — "a trick, perhaps?"`, `Em Dash Delimited Sub-Phrase With a Small Word in Quotes — "A Trick, Perhaps?"`},
		{"Snakes on a Plane — The TV Edit — The Famous Line", "Snakes on a Plane — The TV Edit — The Famous Line"},
		{"EPISODE 7 — THE FORCE AWAKENS", "Episode 7 — The Force Awakens"},
		{"episode 7 – The force awakens", "Episode 7 – The Force Awakens"},
		{"THE CASE OF X ≤ 7", "The Case of X ≤ 7"},
		{"the case of X ≤ 7", "The Case of X ≤ 7"},
		{`"Nothing to Be Afraid of?"`, `"Nothing to Be Afraid Of?"`},
		{`"Nothing to be Afraid Of?"`, `"Nothing to Be Afraid Of?"`},
		{"a thing", "A Thing"},
		{"2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'", "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"},
		{"this is just an example.com", "This Is Just an example.com"},
		{"this is something listed on del.icio.us", "This Is Something Listed on del.icio.us"},
		{"iTunes should be unmolested", "iTunes Should Be Unmolested"},
		{"reading between the lines of steve jobs’s ‘thoughts on music’", "Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’"},
		{"seriously, ‘repair permissions’ is voodoo", "Seriously, ‘Repair Permissions’ Is Voodoo"},
		{"generalissimo francisco franco: still dead; kieren McCarthy: still a jackass", "Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass"},
		{"O'Reilly should be untouched", "O'Reilly Should Be Untouched"},
		{"my name is o'reilly", "My Name Is O'Reilly"},
		{"WASHINGTON, D.C. SHOULD BE FIXED BUT MIGHT BE A PROBLEM", "Washington, D.C. Should Be Fixed but Might Be a Problem"},
		{"THIS IS ALL CAPS AND SHOULD BE ADDRESSED", "This Is All Caps and Should Be Addressed"},
		{"Mr McTavish went to MacDonalds", "Mr McTavish Went to MacDonalds"},
		{"this shouldn't\nget mangled", "This Shouldn't\nGet Mangled"},
		{"this is http://foo.com", "This Is http://foo.com"},
		{"mac mc MAC MC machine", "Mac Mc MAC MC Machine"},
		{"FOO BAR 5TH ST", "Foo Bar 5th St"},
		{"foo bar 5th st", "Foo Bar 5th St"},
		{"l'grange l'grange l'Grange l'Grange", "l'Grange l'Grange l'Grange l'Grange"},
		{"L'grange L'grange L'Grange L'Grange", "l'Grange l'Grange l'Grange l'Grange"},
		{"l'GranGe", "l'GranGe"},
		{"o'grange O'grange o'Grange O'Grange", "O'Grange O'Grange O'Grange O'Grange"},
		{"o'grange's O'grange's o'Grange's O'Grange's", "O'Grange's O'Grange's O'Grange's O'Grange's"},
		{"O'GranGe", "O'GranGe"},
		{"o'melveny/o'doyle o'Melveny/o'doyle O'melveny/o'doyle o'melveny/o'Doyle o'melveny/O'doyle", "O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle O'Melveny/O'Doyle"},
		{"mccay-mcbut-mcdo mcdonalds/mcby", "McCay-McBut-McDo McDonalds/McBy"},
		{"oblon, spivak, mcclelland, maier & neustadt", "Oblon, Spivak, McClelland, Maier & Neustadt"},
		{"Mcoblon, spivak, mcclelland, mcmaier, & mcneustadt", "McOblon, Spivak, McClelland, McMaier, & McNeustadt"},
		{"mcfoo-bar, MCFOO-BAR, McFoo-bar, McFoo-Bar, mcfoo-mcbar, foo-mcbar", "McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-Bar, McFoo-McBar, Foo-McBar"},
		{"'QUOTE' A GREAT", "'Quote' a Great"},
		{"‘QUOTE’ A GREAT", "‘Quote’ a Great"},
		{"“YOUNG AND RESTLESS”", "“Young and Restless”"},
		{"EL NIÑO A ARRIVÉ HIER", "El Niño a Arrivé Hier"},
		{"YEA NO", "Yea No"},
		{"ÝÆ ÑØ", "Ýæ Ñø"},
		{"yea no", "Yea No"},
		{"ýæ ñø", "Ýæ Ñø"},
		{"Mr mr Mrs Ms Mss Dr dr , Mr. and Mrs. Person", "Mr Mr Mrs Ms MSS Dr Dr , Mr. And Mrs. Person"},
		{"a mix\u00a0of\tdifferent\u200aspace\u2006characters", "A Mix\u00a0of\tDifferent\u200aSpace\u2006Characters"},
	}

	for _, tt := range tests {
		actual := Titlecase(tt.input)
		if actual != tt.expected {
			t.Errorf("Titlecase(%q) =\n%q; want\n%q", tt.input, actual, tt.expected)
		}
	}
}

func TestBlankLines(t *testing.T) {
	s1 := "Line number one\n\nand Line three\n"
	want1Default := "Line Number One\nAnd Line Three\n"
	want1Preserve := "Line Number One\n\nAnd Line Three\n"

	if got := Titlecase(s1); got != want1Default {
		t.Errorf("Titlecase(s1) = %q; want %q", got, want1Default)
	}

	opts1 := DefaultOptions()
	opts1.PreserveBlankLines = true
	if got := TitlecaseWithOptions(s1, opts1); got != want1Preserve {
		t.Errorf("TitlecaseWithOptions(s1, preserve) = %q; want %q", got, want1Preserve)
	}

	s2 := "\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n"
	want2Default := "\nLeading Blank\nMulti-Blank\nTrailing Blank\n"
	want2Preserve := "\n\nLeading blank\n\n\nMulti-blank\n\n\n\n\nTrailing Blank\n\n" // preserve blank lines preserves line case of each line
	_ = want2Preserve

	if got := Titlecase(s2); got != want2Default {
		t.Errorf("Titlecase(s2) = %q; want %q", got, want2Default)
	}
}

func TestNewlineEdgeCases(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", ""},
		{"\n", "\n"},
		{"\r\n", "\n"},
		{"\n\n", "\n"},
		{"\r\n\r\n", "\n"},
		{"a", "A"},
		{"\na", "\nA"},
		{"a\n", "A\n"},
		{"\na\n", "\nA\n"},
		{"\r\na\r\n\r\n", "\nA\n"},
		{"a\n\nb", "A\nB"},
		{"   \n  \n ", "   \n  \n "},
	}

	for _, tt := range tests {
		got := Titlecase(tt.input)
		if got != tt.expected {
			t.Errorf("Titlecase(%q) = %q; want %q", tt.input, got, tt.expected)
		}
	}
}

func TestWhitespacePreservation(t *testing.T) {
	s := "text\twith\ttabs"
	if got := Titlecase(s); got != "Text\tWith\tTabs" {
		t.Errorf("Titlecase(%q) = %q; want %q", s, got, "Text\tWith\tTabs")
	}

	opts := DefaultOptions()
	opts.NormaliseSpaceCharacters = true
	if got := TitlecaseWithOptions(s, opts); got != "Text With Tabs" {
		t.Errorf("TitlecaseWithOptions(%q) = %q; want %q", s, got, "Text With Tabs")
	}

	sNBSP := "text\u00a0with\u00a0nonbreaking\u00a0spaces"
	if got := Titlecase(sNBSP); got != "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces" {
		t.Errorf("Titlecase(%q) = %q; want %q", sNBSP, got, "Text\u00a0With\u00a0Nonbreaking\u00a0Spaces")
	}

	// Leading/trailing spaces on a line with small words
	sLeading := "   the great gatsby"
	if got := Titlecase(sLeading); got != "   the Great Gatsby" {
		t.Errorf("Titlecase(%q) = %q; want %q", sLeading, got, "   the Great Gatsby")
	}

	sTrailing := "the great gatsby of   "
	if got := Titlecase(sTrailing); got != "The Great Gatsby of   " {
		t.Errorf("Titlecase(%q) = %q; want %q", sTrailing, got, "The Great Gatsby of   ")
	}
}

func TestCallbacks(t *testing.T) {
	cb := func(word string, allCaps bool) string {
		switch strings.ToUpper(word) {
		case "TCP", "UDP":
			return strings.ToUpper(word)
		default:
			return ""
		}
	}

	opts := DefaultOptions()
	opts.Callback = cb

	s := "a simple tcp and udp wrapper"
	want := "A Simple TCP and UDP Wrapper"
	if got := TitlecaseWithOptions(s, opts); got != want {
		t.Errorf("TitlecaseWithOptions(%q) = %q; want %q", s, got, want)
	}

	// Immutable callback word at the beginning of string
	cbThe := func(word string, allCaps bool) string {
		if word == "the" {
			return "the"
		}
		return ""
	}
	optsThe := DefaultOptions()
	optsThe.Callback = cbThe
	if got := TitlecaseWithOptions("the great gatsby", optsThe); got != "the Great Gatsby" {
		t.Errorf("Immutable callback failed: got %q, want %q", got, "the Great Gatsby")
	}
}

func TestInitialsRegex(t *testing.T) {
	if !reUCInitials.MatchString("A.B") {
		t.Errorf("reUCInitials should match A.B")
	}
	if !reUCInitials.MatchString("A.B.") {
		t.Errorf("reUCInitials should match A.B.")
	}
	if reUCInitials.MatchString("ABCD") {
		t.Errorf("reUCInitials should not match ABCD")
	}
}

