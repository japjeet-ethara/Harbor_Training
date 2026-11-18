package format

import p "komal/titlecase/internal/pattern"

const punctuation = "!\"“#$%&'‘()*+,-–‒—―./:;?@[\\]_`{|}~"

func small() p.Node {
	words := []string{"a", "an", "and", "as", "at", "but", "by", "en", "for", "if", "in", "of", "on", "or", "the", "to"}
	nodes := []p.Node{}
	for _, w := range words {
		nodes = append(nodes, p.Text(w))
	}
	return p.Alt(append(nodes,
		p.Seq(p.Text("v"), p.Rep(p.Chars("."), 0, 1, false)),
		p.Text("via"),
		p.Seq(p.Text("vs"), p.Rep(p.Chars("."), 0, 1, false)))...)
}

var patterns = map[string]p.Program{
	"lines":      p.Compile(p.Rep(p.Chars("\r\n"), 1, -1, false)),
	"spaces":     p.Compile(p.Cap(1, p.Prop("space"))),
	"small":      p.Compile(p.CI(p.Seq(p.Assert(p.Start), p.Cap(1, small()), p.Assert(p.End)))),
	"first":      p.Compile(p.CI(p.Seq(p.Assert(p.Start), p.Cap(1, p.Rep(p.Chars(punctuation), 0, -1, false)), p.Cap(2, small()), p.Assert(p.Boundary)))),
	"last":       p.Compile(p.CI(p.Seq(p.Assert(p.Boundary), p.Cap(1, small()), p.Rep(p.Chars(punctuation), 0, 1, false), p.Assert(p.End)))),
	"subphrase":  p.Compile(p.Seq(p.Cap(1, p.Seq(p.Chars(":.;?!-–‒—―"), p.Text(" "))), p.Cap(2, small()))),
	"mc":         p.Compile(p.Seq(p.Assert(p.Start), p.Cap(1, p.Alt(p.Seq(p.Chars("Mm"), p.Text("c")), p.Text("MC"))), p.Cap(2, p.Seq(p.Prop("word"), p.Rep(p.Prop("dot"), 1, -1, false))))),
	"honorific":  p.Compile(p.CI(p.Seq(p.Assert(p.Start), p.Cap(1, p.Alt(p.Cap(2, p.Seq(p.Text("m"), p.Cap(3, p.Alt(p.Cap(4, p.Seq(p.Text("r"), p.Rep(p.Text("s"), 0, 1, false))), p.Text("s"))))), p.Text("Dr"))), p.Assert(p.End)))),
	"inline":     p.Compile(p.Seq(p.Prop("word"), p.Text("."), p.Prop("word"))),
	"internal":   p.Compile(p.Seq(p.Rep(p.Chars(punctuation), 0, -1, true), p.Rep(p.Chars("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"), 1, -1, false), p.Rep(p.Chars("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), 1, -1, true))),
	"cap":        p.Compile(p.Seq(p.Assert(p.Start), p.Rep(p.Chars(punctuation), 0, -1, true), p.Cap(1, p.Prop("word")))),
	"apostrophe": p.Compile(p.CI(p.Seq(p.Assert(p.Start), p.Chars("dol"), p.Chars("'‘"), p.Rep(p.Prop("word"), 1, -1, false), p.Rep(p.Rep(p.Chars("'s"), 2, 2, false), 0, 1, false), p.Assert(p.End)))),
	"initials":   p.Compile(p.Seq(p.Assert(p.Start), p.Rep(p.Alt(p.Seq(p.Chars("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), p.Text(".")), p.Seq(p.Chars("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), p.Text("."), p.Chars("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))), 1, -1, false), p.Assert(p.End))),
	"consonants": p.Compile(p.CI(p.Seq(p.Assert(p.Start), p.Rep(p.Chars("bcdfghjklmnpqrstvwxz"), 1, -1, false), p.Assert(p.StrictEnd)))),
}
