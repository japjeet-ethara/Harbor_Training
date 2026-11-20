FROM golang:1.23

# Copy of ../../python-titlecase (commit 42f43e2), WITHOUT .git and NOTES.md
# (so the agent cannot see our notes).
# Docker can only COPY from inside the build context (this folder),
# so the repo was copied into environment/repo/ first.
COPY repo/ /workspace/repo/

WORKDIR /workspace/repo
