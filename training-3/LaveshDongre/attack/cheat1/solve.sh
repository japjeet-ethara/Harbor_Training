#!/bin/bash
set -euo pipefail

solution=/workspace/repo/solution/solve.sh
if [[ ! -f "$solution" ]]; then
	echo "The bundled solution script is not available in the workspace." >&2
	exit 1
fi

sed 's/\r$//' "$solution" | bash
