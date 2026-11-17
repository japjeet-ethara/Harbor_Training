#!/bin/bash
# The examiner. Harbor copies this folder to /tests after the agent has finished, then runs this script.
# The grader is a Go program because the room has no Python; it needs no internet.
cd /tests && go run grade.go
