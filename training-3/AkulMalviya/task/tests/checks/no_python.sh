cd /workspace/repo || reject 'Missing submission workspace'
invalid=$(find . ! -type d ! -type f -print -quit) ||
  reject 'Cannot inspect submission workspace'
[[ -z "$invalid" ]] || reject 'Submission contains a link or special file'
python=$(find . -type f -iname '*.py' -print -quit) ||
  reject 'Cannot inspect submission source'
[[ -z "$python" ]] || reject 'Submission contains Python source'
[[ -f go.mod && ! -e vendor ]] || reject 'Expected a Go module without vendored dependencies'
