// godump_classes prints, for every code point where either is true, the oracle's
// Go base rules for \w (r == '_' || unicode.IsLetter || unicode.IsNumber) and
// \s (unicode.IsSpace), so mkclasses.py can list where Python differs.
// Columns: code point (hex), word 0/1, space 0/1.
package main

import (
	"bufio"
	"fmt"
	"os"
	"unicode"
)

func main() {
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	fmt.Fprintf(w, "# go unicode.Version %s\n", unicode.Version)
	for r := rune(0); r <= unicode.MaxRune; r++ {
		if r >= 0xD800 && r <= 0xDFFF {
			continue
		}
		word := r == '_' || unicode.IsLetter(r) || unicode.IsNumber(r)
		space := unicode.IsSpace(r)
		if !word && !space {
			continue
		}
		b := func(x bool) int {
			if x {
				return 1
			}
			return 0
		}
		fmt.Fprintf(w, "%X\t%d\t%d\n", r, b(word), b(space))
	}
}
