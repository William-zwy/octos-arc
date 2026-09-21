#!/bin/sh
# Build a commit-bound ARC platform Agent ZIP (main.py must be at ZIP root).
set -eu
cd "$(dirname "$0")"

commit=$(git rev-parse HEAD)
short_commit=$(git rev-parse --short=12 HEAD)
output=${1:-../octos-arc-bundle-${short_commit}.zip}
case "$output" in
  /*) ;;
  *) output="$(pwd)/$output" ;;
esac

if [ -e "$output" ]; then
  echo "error: refusing to overwrite existing artifact: $output" >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1; then
  python_cmd=python3
elif command -v python >/dev/null 2>&1; then
  python_cmd=python
else
  echo "error: python3 or python is required for the package-shape gate" >&2
  exit 3
fi

git archive --format=zip --output="$output" HEAD:arc -- \
  main.py octos_stdio.py requirement_order.py acceptance.py guard.py \
  llm_proxy.py codegen.py package_shape.py hooks requirements.txt \
  arcbench_agent_runtime public-tests

"$python_cmd" package_shape.py agent --archive "$output" --output "${output%.zip}.shape.json" >/dev/null
echo "commit=$commit"
echo "artifact=$output"
shasum -a 256 "$output"
