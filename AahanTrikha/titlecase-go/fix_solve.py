#!/usr/bin/env python3
"""Fix the mcName bug in solve.sh"""

import base64
import re

# Read current solve.sh
with open('solution/solve.sh', 'r') as f:
    solve_content = f.read()

# Extract base64 code
match = re.search(r"printf '%s' ([A-Za-z0-9+/=]+)", solve_content)
if not match:
    print("Could not find base64 code!")
    exit(1)

b64_code = match.group(1)
go_code = base64.b64decode(b64_code).decode('utf-8')

# Save original for reference
with open('main.go.original', 'w') as f:
    f.write(go_code)

print("Original mcName function:")
# Find and show mcName function
mcname_start = go_code.find('func mcName(')
if mcname_start != -1:
    mcname_end = go_code.find('\n}', mcname_start) + 2
    print(go_code[mcname_start:mcname_end])

# Fix the bug: change titlecase(..., true) to titlecase(..., false) in mcName
# The line should be: return pyCap(prefix) + titlecase(string(r[2:]), false), true
go_code_fixed = go_code.replace(
    'return pyCap(prefix) + titlecase(string(r[2:]), true), true',
    'return pyCap(prefix) + titlecase(string(r[2:]), false), true'
)

# Check if fix was applied
if go_code == go_code_fixed:
    print("\n⚠️  WARNING: No changes made - pattern not found!")
    print("Looking for alternative patterns...")
    
    # Try alternative: look for the pattern more carefully
    if 'titlecase(string(r[2:])' in go_code:
        # Find context around this call
        idx = go_code.find('titlecase(string(r[2:])')
        print(f"\nFound at position {idx}:")
        print(go_code[max(0, idx-50):idx+100])
else:
    print("\n✅ Fixed mcName recursive call parameter")

# Save fixed version
with open('main.go.fixed', 'w') as f:
    f.write(go_code_fixed)

# Re-encode
b64_fixed = base64.b64encode(go_code_fixed.encode('utf-8')).decode('ascii')

# Update solve.sh
solve_content_fixed = solve_content.replace(b64_code, b64_fixed)

# Backup original
with open('solution/solve.sh.backup', 'w') as f:
    f.write(solve_content)

# Write fixed version
with open('solution/solve.sh', 'w') as f:
    f.write(solve_content_fixed)

print("\n✅ Updated solution/solve.sh")
print("✅ Backup saved to solution/solve.sh.backup")
print("\nNow run: uvx harbor run -p . -a oracle")
