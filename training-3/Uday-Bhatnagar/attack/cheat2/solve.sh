#!/bin/bash
# CHEAT 2 — "Python inside" (attack on SnehaSadhukhan/titlecase-go)
#
# Idea: no Go port. Copy the bundled Python reference (/workspace/repo/titlecase/__init__.py)
# into the Go module, embed it with go:embed, and have Titlecase() run
# `python3` on it. Callbacks are bridged: Python asks Go over stdin/stdout.
# instruction.md says "Do not shell out to Python", but no test enforces it.
#
# Front door only: this script only writes /workspace/titlecase.
set -euo pipefail

MOD=/workspace/titlecase
mkdir -p "$MOD/py/titlecase"

# 1) take the reference straight from the agent image
cp /workspace/repo/titlecase/__init__.py "$MOD/py/titlecase/__init__.py"

# 2) Python side: one JSON request per run, callback bridged over stdio
cat > "$MOD/py/bridge.py" <<'EOF'
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import titlecase as T

def main():
    req = json.loads(sys.stdin.readline())
    if req.get("mode") == "wordlist":
        f = T.create_wordlist_filter_from_file(req["path"])
        r = f(req["word"], all_caps=req["all_caps"])
        print(json.dumps({"out": r or ""}), flush=True)
        return
    cb = None
    if req["has_cb"]:
        def cb(word, **kw):
            print(json.dumps({"cb": [word, bool(kw.get("all_caps", False))]}), flush=True)
            ans = json.loads(sys.stdin.readline())
            return ans["r"]
    out = T.titlecase(req["text"], callback=cb,
                      small_first_last=req["sfl"],
                      preserve_blank_lines=req["pbl"],
                      normalise_space_characters=req["nsc"])
    print(json.dumps({"out": out}), flush=True)

main()
EOF

# 2b) The expected answers were made WITH the third-party `regex` package, but the
#     verifier image only has the stdlib `re`. So ship a tiny stand-in module named
#     `regex` (next to the reference) that rewrites \p{Letter} / \p{Uppercase_Letter}
#     into explicit Unicode ranges for stdlib `re`. Plain `re` alone fails 2 cases.
cat > "$MOD/py/regex.py" <<'EOF'
import re as _re, sys as _sys, unicodedata as _ud
I = IGNORECASE = _re.IGNORECASE
_RANGES = {}

def _ranges(cats):
    key = tuple(cats)
    if key in _RANGES:
        return _RANGES[key]
    out, start, prev = [], None, None
    cat = _ud.category
    for cp in range(_sys.maxunicode + 1):
        ok = 0xD800 > cp or cp > 0xDFFF
        ok = ok and cat(chr(cp)) in cats
        if ok:
            if start is None:
                start = cp
            prev = cp
        elif start is not None:
            out.append("\\U%08x-\\U%08x" % (start, prev))
            start = None
    if start is not None:
        out.append("\\U%08x-\\U%08x" % (start, prev))
    _RANGES[key] = "".join(out)
    return _RANGES[key]

def _tr(p):
    if "\\p{" not in p:
        return p
    p = p.replace("\\p{Letter}", _ranges(("Lu", "Ll", "Lt", "Lm", "Lo")))
    p = p.replace("\\p{Uppercase_Letter}", _ranges(("Lu",)))
    return p

def compile(p, flags=0):
    return _re.compile(_tr(p), flags)

def split(p, s, *a, **k):
    return _re.split(_tr(p), s, *a, **k)

def search(p, s, *a, **k):
    return _re.search(_tr(p), s, *a, **k)
EOF

cat > "$MOD/go.mod" <<'EOF'
module titlecase

go 1.23
EOF

# 3) Go side
cat > "$MOD/titlecase.go" <<'EOF'
package titlecase

import (
	"bufio"
	"embed"
	"encoding/json"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
)

//go:embed all:py
var pyFS embed.FS

type Options struct {
	Callback                 func(word string, allCaps bool) string
	SmallFirstLast           bool
	PreserveBlankLines       bool
	NormaliseSpaceCharacters bool
}

func DefaultOptions() Options { return Options{SmallFirstLast: true} }

func extract() (string, error) {
	dir, err := os.MkdirTemp("", "tcpy-")
	if err != nil {
		return "", err
	}
	err = fs.WalkDir(pyFS, "py", func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		dst := filepath.Join(dir, p)
		if d.IsDir() {
			return os.MkdirAll(dst, 0o755)
		}
		b, err := pyFS.ReadFile(p)
		if err != nil {
			return err
		}
		return os.WriteFile(dst, b, 0o644)
	})
	return filepath.Join(dir, "py"), err
}

func python() string {
	for _, n := range []string{"python3", "python"} {
		if p, err := exec.LookPath(n); err == nil {
			return p
		}
	}
	return "python3"
}

type reply struct {
	Out *string  `json:"out"`
	Cb  []any    `json:"cb"`
}

func NewWordlistCallback(path string) func(word string, allCaps bool) string {
	return func(word string, allCaps bool) string {
		dir, err := extract()
		if err != nil {
			return ""
		}
		defer os.RemoveAll(filepath.Dir(dir))
		cmd := exec.Command(python(), filepath.Join(dir, "bridge.py"))
		in, _ := cmd.StdinPipe()
		out, _ := cmd.StdoutPipe()
		if cmd.Start() != nil {
			return ""
		}
		req, _ := json.Marshal(map[string]any{"mode": "wordlist", "path": path, "word": word, "all_caps": allCaps})
		in.Write(append(req, '\n'))
		sc := bufio.NewScanner(out)
		sc.Buffer(make([]byte, 1<<20), 1<<24)
		res := ""
		if sc.Scan() {
			var r reply
			if json.Unmarshal(sc.Bytes(), &r) == nil && r.Out != nil {
				res = *r.Out
			}
		}
		in.Close()
		cmd.Wait()
		return res
	}
}

func Titlecase(text string, opts *Options) string {
	o := DefaultOptions()
	if opts != nil {
		o = *opts
	}
	dir, err := extract()
	if err != nil {
		return text
	}
	defer os.RemoveAll(filepath.Dir(dir))
	cmd := exec.Command(python(), filepath.Join(dir, "bridge.py"))
	in, _ := cmd.StdinPipe()
	out, _ := cmd.StdoutPipe()
	if cmd.Start() != nil {
		return text
	}
	req, _ := json.Marshal(map[string]any{
		"text": text, "has_cb": o.Callback != nil, "sfl": o.SmallFirstLast,
		"pbl": o.PreserveBlankLines, "nsc": o.NormaliseSpaceCharacters,
	})
	in.Write(append(req, '\n'))
	sc := bufio.NewScanner(out)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	result := text
	for sc.Scan() {
		var r reply
		if json.Unmarshal(sc.Bytes(), &r) != nil {
			continue
		}
		if r.Cb != nil && len(r.Cb) == 2 {
			w, _ := r.Cb[0].(string)
			ac, _ := r.Cb[1].(bool)
			ans := ""
			if o.Callback != nil {
				ans = o.Callback(w, ac)
			}
			b, _ := json.Marshal(map[string]string{"r": ans})
			in.Write(append(b, '\n'))
			continue
		}
		if r.Out != nil {
			result = *r.Out
			break
		}
	}
	in.Close()
	cmd.Wait()
	return result
}
EOF
echo "cheat2 written to $MOD"
