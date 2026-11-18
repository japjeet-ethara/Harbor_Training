# titlecase-go progress

## Done
- Environment image: Go 1.23, Python titlecase at `/workspace/repo`. Agent image has no `/tests`.
- Instruction, notes, and 2,000/2,000 datasets are in place. Expected bytes came from the original Python path with the optional `regex` package absent.
- Verifier weights are unchanged: `build` 1, `no_python` 1, `behavior` 4, weighted mean `reward`.
- `behavior` compares the program only with `hidden_input.txt` and `hidden_expected.txt`.
- `no_python` is 1 only when the tree has no `.py` file and `go build ./...` succeeds.
- Correct Go solution remains in `solution/`. Backup in `titlecase-go-solution-backup` matches it.
- Temporary cheat in `titlecase-go-cheat-solution` is a visible-pair lookup. It echoes unknown lines and does not delete `.py` files.

## Harbor oracle results
- Cheat trial `titlecase-go__2qtmu5h`: `build` 1.0, `no_python` 0.0, `behavior` 0.0, `reward` 0.1667.
- Restored solution trial `titlecase-go__BZNvxZT`: `build` 1.0, `no_python` 1.0, `behavior` 1.0, `reward` 1.0.

## Remaining
- None for the oracle. The agent image still starts from the Python tree.
