FROM golang:1.23

# No Python in the agent image: the port has to be written, not wrapped,
# and the original cannot be run to produce answers.
RUN apt-get purge -y --auto-remove 'python3*' 'libpython3*' \
 && rm -rf /var/lib/apt/lists/*

# Copy of ../../python-titlecase (commit 42f43e2), WITHOUT .git and NOTES.md
# (so the agent cannot see our notes).
# Docker can only COPY from inside the build context (this folder),
# so the repo was copied into environment/repo/ first.
COPY repo/ /workspace/repo/

WORKDIR /workspace/repo
