#!/bin/bash
# Find differences between Go output and expected output

cd /workspace/repo

# Build the Go program
go build -o titlecase-bin . || exit 1

# Run it and compare
./titlecase-bin < /tests/data/hidden_inputs.txt > /tmp/go_output.txt

# Find first 10 differences
python3 << 'EOF'
with open('/tests/data/hidden_inputs.txt') as f:
    inputs = f.readlines()
with open('/tests/data/hidden_expected.txt') as f:
    expected = f.readlines()
with open('/tmp/go_output.txt') as f:
    actual = f.readlines()

diffs = 0
for i, (inp, exp, act) in enumerate(zip(inputs, expected, actual), 1):
    if exp != act:
        print(f"\nLine {i}:")
        print(f"  Input:    {inp.rstrip()!r}")
        print(f"  Expected: {exp.rstrip()!r}")
        print(f"  Actual:   {act.rstrip()!r}")
        diffs += 1
        if diffs >= 10:
            break

print(f"\nTotal lines checked: {len(inputs)}")
print(f"Differences found: {sum(1 for e, a in zip(expected, actual) if e != a)}")
EOF
