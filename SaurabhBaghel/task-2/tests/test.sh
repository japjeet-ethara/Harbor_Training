#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
cd /tests && go run grade.go
