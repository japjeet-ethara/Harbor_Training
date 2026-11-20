# Cheat 2 - Python Inside

## Verified findings
- Python 3 and pip are installed in the Docker image.
- The original Python titlecase source is copied into /workspace/repo/.
- The package CLI entry point is titlecase.__init__:cmd.
- The optional regex dependency falls back to Python re.
- The no_python criterion checks for files ending in .py.

## Experiment status
Not yet implemented.
No Harbor score recorded.
