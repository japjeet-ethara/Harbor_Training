#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
go_bin="/home/charitra/.local/opt/go1.23.12/bin/go"
suite="$root/tests/data"
old_suite="$root/measure/old-exam"
out="$root/measure"

GOTOOLCHAIN=local GOPROXY=off "$go_bin" -C "$root/solution" build -o "$out/charitra-port" .
"$out/charitra-port" < "$suite/inputs.txt" > "$out/charitra-output.txt"

GOTOOLCHAIN=local GOPROXY=off "$go_bin" -C "$root/measure/ports/MadhurJain" build -o "$out/madhur-port" .
"$out/madhur-port" < "$suite/inputs.txt" > "$out/madhur-output.txt"

GO111MODULE=off GOTOOLCHAIN=local GOPROXY=off "$go_bin" -C "$root/measure/ports/LokeshDeshwal" build -o "$out/lokesh-port" .
"$out/lokesh-port" < "$suite/inputs.txt" > "$out/lokesh-output.txt"

"$out/charitra-port" < "$old_suite/inputs.txt" > "$out/charitra-old-output.txt"
"$out/madhur-port" < "$old_suite/inputs.txt" > "$out/madhur-old-output.txt"
"$out/lokesh-port" < "$old_suite/inputs.txt" > "$out/lokesh-old-output.txt"

python3 "$root/kit/compare.py" "$suite" "$out/charitra-output.txt"
python3 "$root/kit/compare.py" "$suite" "$out/madhur-output.txt"
python3 "$root/kit/compare.py" "$suite" "$out/lokesh-output.txt"
python3 "$root/kit/compare.py" "$old_suite" "$out/charitra-old-output.txt"
python3 "$root/kit/compare.py" "$old_suite" "$out/madhur-old-output.txt"
python3 "$root/kit/compare.py" "$old_suite" "$out/lokesh-old-output.txt"
