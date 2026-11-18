#!/bin/bash
set -euo pipefail

cd /tests && go run grade.go
