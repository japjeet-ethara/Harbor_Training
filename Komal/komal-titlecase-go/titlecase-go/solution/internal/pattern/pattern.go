package pattern

import (
	"strings"

	"komal/titlecase/internal/pyunicode"
)

type Kind uint8

const (
	Empty Kind = iota
	Class
	Sequence
	Alternative
	Repeat
	Capture
	Start
	End
	StrictEnd
	Boundary
)

type Node struct {
	Kind        Kind
	Set         string
	Property    string
	Insensitive bool
	Children    []Node
	Min, Max    int
	Lazy        bool
	Group       int
}

func Chars(s string) Node { return Node{Kind: Class, Set: s} }
func Prop(s string) Node  { return Node{Kind: Class, Property: s} }
func CI(n Node) Node {
	n.Insensitive = true
	for i := range n.Children {
		n.Children[i] = CI(n.Children[i])
	}
	return n
}
func Text(s string) Node {
	var ns []Node
	for _, r := range s {
		ns = append(ns, Chars(string(r)))
	}
	return Seq(ns...)
}
func Seq(ns ...Node) Node { return Node{Kind: Sequence, Children: ns} }
func Alt(ns ...Node) Node { return Node{Kind: Alternative, Children: ns} }
func Rep(n Node, min, max int, lazy bool) Node {
	return Node{Kind: Repeat, Children: []Node{n}, Min: min, Max: max, Lazy: lazy}
}
func Cap(group int, n Node) Node { return Node{Kind: Capture, Group: group, Children: []Node{n}} }
func Assert(k Kind) Node         { return Node{Kind: k} }

type operation uint8

const (
	consume operation = iota
	split
	jump
	save
	assertion
	accept
)

type instruction struct {
	op   operation
	node Node
	x, y int
}

type Program struct{ code []instruction }

func nullable(n Node) bool {
	switch n.Kind {
	case Class:
		return false
	case Sequence:
		for _, c := range n.Children {
			if !nullable(c) {
				return false
			}
		}
		return true
	case Alternative:
		for _, c := range n.Children {
			if nullable(c) {
				return true
			}
		}
		return false
	case Repeat:
		return n.Min == 0 || nullable(n.Children[0])
	case Capture:
		return nullable(n.Children[0])
	default:
		return true
	}
}

func Compile(n Node) Program {
	p := Program{}
	p.emit(n)
	p.code = append(p.code, instruction{op: accept})
	return p
}

func (p *Program) emit(n Node) {
	switch n.Kind {
	case Empty:
	case Class:
		p.code = append(p.code, instruction{op: consume, node: n})
	case Sequence:
		for _, c := range n.Children {
			p.emit(c)
		}
	case Alternative:
		var ends []int
		for i, c := range n.Children {
			if i == len(n.Children)-1 {
				p.emit(c)
				break
			}
			at := len(p.code)
			p.code = append(p.code, instruction{op: split, x: at + 1})
			p.emit(c)
			ends = append(ends, len(p.code))
			p.code = append(p.code, instruction{op: jump})
			p.code[at].y = len(p.code)
		}
		for _, at := range ends {
			p.code[at].x = len(p.code)
		}
	case Repeat:
		if n.Max < 0 && nullable(n.Children[0]) {
			panic("unbounded repetition of nullable pattern")
		}
		for i := 0; i < n.Min; i++ {
			p.emit(n.Children[0])
		}
		if n.Max < 0 {
			at := len(p.code)
			p.code = append(p.code, instruction{op: split, x: at + 1})
			p.emit(n.Children[0])
			p.code = append(p.code, instruction{op: jump, x: at})
			p.code[at].y = len(p.code)
			if n.Lazy {
				p.code[at].x, p.code[at].y = p.code[at].y, p.code[at].x
			}
		} else {
			for i := n.Min; i < n.Max; i++ {
				at := len(p.code)
				p.code = append(p.code, instruction{op: split, x: at + 1})
				p.emit(n.Children[0])
				p.code[at].y = len(p.code)
				if n.Lazy {
					p.code[at].x, p.code[at].y = p.code[at].y, p.code[at].x
				}
			}
		}
	case Capture:
		if n.Group < 1 || n.Group > 5 {
			panic("capture out of range")
		}
		p.code = append(p.code, instruction{op: save, x: 2 * n.Group})
		p.emit(n.Children[0])
		p.code = append(p.code, instruction{op: save, x: 2*n.Group + 1})
	default:
		p.code = append(p.code, instruction{op: assertion, node: n})
	}
}

type Match struct {
	Input     []rune
	Positions [12]int
}

func (m Match) Start() int { return m.Positions[0] }
func (m Match) End() int   { return m.Positions[1] }
func (m Match) Group(n int) string {
	a, b := m.Positions[2*n], m.Positions[2*n+1]
	if a < 0 || b < 0 {
		return ""
	}
	return string(m.Input[a:b])
}

func classMatches(n Node, r rune) bool {
	switch n.Property {
	case "word":
		return pyunicode.Word(r)
	case "space":
		return pyunicode.Space(r)
	case "dot":
		return r != '\n'
	}
	if !n.Insensitive {
		return strings.ContainsRune(n.Set, r)
	}
	r = pyunicode.Fold(r)
	for _, c := range n.Set {
		if pyunicode.Fold(c) == r {
			return true
		}
	}
	return false
}

func (p Program) execute(rs []rune, pc, pos int, caps [12]int) (Match, bool) {
	for {
		inst := p.code[pc]
		switch inst.op {
		case consume:
			if pos == len(rs) || !classMatches(inst.node, rs[pos]) {
				return Match{}, false
			}
			pos++
			pc++
		case jump:
			pc = inst.x
		case split:
			if m, ok := p.execute(rs, inst.x, pos, caps); ok {
				return m, true
			}
			pc = inst.y
		case save:
			caps[inst.x] = pos
			pc++
		case assertion:
			ok := false
			switch inst.node.Kind {
			case Start:
				ok = pos == 0
			case End:
				ok = pos == len(rs) || (pos == len(rs)-1 && rs[pos] == '\n')
			case StrictEnd:
				ok = pos == len(rs)
			case Boundary:
				left := pos > 0 && pyunicode.Word(rs[pos-1])
				right := pos < len(rs) && pyunicode.Word(rs[pos])
				ok = left != right
			}
			if !ok {
				return Match{}, false
			}
			pc++
		case accept:
			caps[1] = pos
			return Match{rs, caps}, true
		}
	}
}

func (p Program) at(rs []rune, start int) (Match, bool) {
	var caps [12]int
	for i := range caps {
		caps[i] = -1
	}
	caps[0] = start
	return p.execute(rs, 0, start, caps)
}

func (p Program) Match(s string) (Match, bool) { return p.at([]rune(s), 0) }
func (p Program) Search(s string) (Match, bool) {
	rs := []rune(s)
	for i := 0; i <= len(rs); i++ {
		if m, ok := p.at(rs, i); ok {
			return m, true
		}
	}
	return Match{}, false
}

func (p Program) Replace(s string, fn func(Match) string) string {
	rs := []rune(s)
	var out strings.Builder
	last := 0
	for i := 0; i <= len(rs); {
		m, ok := p.at(rs, i)
		if !ok {
			i++
			continue
		}
		if m.End() == i {
			panic("empty substitutions are outside this engine's contract")
		}
		out.WriteString(string(rs[last:i]))
		out.WriteString(fn(m))
		last = m.End()
		i = last
	}
	out.WriteString(string(rs[last:]))
	return out.String()
}

func (p Program) Split(s string, captures bool) []string {
	rs := []rune(s)
	parts := []string{}
	last := 0
	for i := 0; i <= len(rs); {
		m, ok := p.at(rs, i)
		if !ok {
			i++
			continue
		}
		if m.End() == i {
			panic("empty splits are outside this engine's contract")
		}
		parts = append(parts, string(rs[last:i]))
		if captures {
			parts = append(parts, m.Group(1))
		}
		last = m.End()
		i = last
	}
	return append(parts, string(rs[last:]))
}
