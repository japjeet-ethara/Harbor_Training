// godump prints Go's own casing facts for every code point that has any, so that
// mkcasing.py can list where Python's full case mappings differ from them.
// Columns (hex): code point, unicode.ToUpper, unicode.ToLower, unicode.ToTitle,
// then 0/1 flags: Mn Me Cf Lm Sk Lu Ll Lt Other_Lowercase Other_Uppercase.
package main

import (
	"bufio"
	"fmt"
	"os"
	"unicode"
)

func b(x bool) int {
	if x {
		return 1
	}
	return 0
}

func main() {
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	fmt.Fprintf(w, "# go unicode.Version %s\n", unicode.Version)
	for r := rune(0); r <= unicode.MaxRune; r++ {
		if r >= 0xD800 && r <= 0xDFFF {
			continue
		}
		u, l, t := unicode.ToUpper(r), unicode.ToLower(r), unicode.ToTitle(r)
		f := []bool{
			unicode.Is(unicode.Mn, r), unicode.Is(unicode.Me, r), unicode.Is(unicode.Cf, r),
			unicode.Is(unicode.Lm, r), unicode.Is(unicode.Sk, r), unicode.IsUpper(r),
			unicode.IsLower(r), unicode.IsTitle(r), unicode.Is(unicode.Other_Lowercase, r),
			unicode.Is(unicode.Other_Uppercase, r),
		}
		any := u != r || l != r || t != r
		for _, x := range f {
			any = any || x
		}
		if !any {
			continue
		}
		fmt.Fprintf(w, "%X\t%X\t%X\t%X", r, u, l, t)
		for _, x := range f {
			fmt.Fprintf(w, "\t%d", b(x))
		}
		fmt.Fprintln(w)
	}
}
