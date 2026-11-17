FROM golang:1.23

# python-titlecase is exported from upstream commit
# 42f43e2de55bf003b286c6f8e8d8b2d26676a167 with `git archive`, so it has no .git.
# Docker can only copy from the build context, which is this folder.
COPY python-titlecase /workspace/repo

WORKDIR /workspace/repo
