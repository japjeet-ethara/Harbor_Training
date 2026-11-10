# What the repository is

This repository is a Python library that changes a given text to Title Caps, and attempts to be clever about small words such as a, an, and the. The list of small words which are not capitalized comes from the New York Times Manual of Style, plus some others such as vs and v. It uses heuristics to guess abbreviations that do not need conversion. The library is a resurrection of Stuart Colville's titlecase.py, itself a port of John Gruber's titlecase.pl, and is released under the MIT License.

# What to build

Build a Go program in `/workspace/repo`. It must read one title per line from standard input and print the titlecased result, one per line.

# Hard rules

Use the Go standard library only. Do not leave any `.py` files anywhere in the repository. `go build ./...` must pass.

# Behaviour

For every input, the output must match the original Python `titlecase()` function byte for byte.

# Not checked

Speed, memory use, and the wording of error messages are not checked.

# How it is graded

Hidden automatic tests grade the program. A partial score is possible.
