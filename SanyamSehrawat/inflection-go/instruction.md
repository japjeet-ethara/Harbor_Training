# Port inflection to Go

## The repository

`/workspace/repo` contains inflection 0.5.1, a Python port of the Ruby on Rails inflector. Its
functions, in `inflection/__init__.py`, change the form of words and identifiers: singular and
plural nouns (`octopus` and `octopi`), CamelCase and snake_case names, human-readable titles,
URL slugs and ordinal numbers.

## What to build

Replace the Python implementation with a Go program in `/workspace/repo`.

- `/workspace/repo` must be the root of a Go module whose root package is `package main`.
  Running `go build -o /tmp/inflection .` in `/workspace/repo` must produce the program.
- The program reads standard input. Every input line ends with `\n` and has the form
  `<function>\t<argument>`: a function name, one tab character, then the argument (which may
  be empty).
- For each input line, in order, it writes the result followed by `\n` to standard output. The
  output has exactly one line per input line.
- The program takes no command-line arguments.

The function names, and the call to the original each one stands for:

| Function name | Result must equal |
|---|---|
| `camelize` | `camelize(argument)` |
| `camelize_lower` | `camelize(argument, False)` |
| `dasherize` | `dasherize(argument)` |
| `humanize` | `humanize(argument)` |
| `ordinalize` | `ordinalize(int(argument))` |
| `parameterize` | `parameterize(argument)` |
| `parameterize_underscore` | `parameterize(argument, '_')` |
| `pluralize` | `pluralize(argument)` |
| `singularize` | `singularize(argument)` |
| `tableize` | `tableize(argument)` |
| `titleize` | `titleize(argument)` |
| `underscore` | `underscore(argument)` |

## Hard rules

- Use the Go standard library only: `go.mod` has no `require` or `replace` line, and there is no
  cgo. The program must build with the Go 1.23 toolchain in this image with no network access
  (`GOTOOLCHAIN=local`, `GOPROXY=off`, `GOFLAGS=-mod=mod`, `CGO_ENABLED=0`).
- `go build ./...` must pass in `/workspace/repo`.
- The program must do the work itself. It reads only standard input; it must not read other
  files, run any other program (for example a Python interpreter) or use the network. It is run
  as an unprivileged user.
- When you finish, no `.py` file may be left anywhere under `/workspace/repo`.

## Behaviour

Each output line must equal, byte for byte, the result of the call in the table above, made on
the original library in this repository. Python 3 is installed in this image, so you can run the
original to see what it returns.

Arguments contain only printable ASCII characters (space to `~`); they never contain a tab or
any other control character. For `ordinalize` the argument is an optional `-` followed by one
or more decimal digits; it may have leading zeros and may be too large for a 64-bit integer.
For `camelize_lower` the argument is never empty. Every input line uses one of the function
names above.

## Not checked

Speed, memory use, the wording of error messages, and behaviour on input that breaks the rules
above.

## How it is graded

Hidden automatic tests give a score from 0 to 1 with partial credit: one part for the build,
one part for the removal of the Python files (counted only if the build passes), and four parts
for the share of hidden input lines whose output line matches the original exactly.
