#!/bin/sh
# Build a commit-bound ARC platform Agent ZIP (main.py must be at ZIP root).
set -eu
PATH="/usr/bin:/bin:/mingw64/bin:$PATH"
export PATH
case "$0" in
  */*) script_parent=${0%/*} ;;
  *) script_parent=. ;;
esac
script_dir=$(CDPATH= cd -- "$script_parent" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
cd "$script_dir"

commit=$(git -C "$repo_root" rev-parse HEAD)
short_commit=$(git -C "$repo_root" rev-parse --short=12 HEAD)
output=${1:-../octos-arc-bundle-${short_commit}.zip}
case "$output" in
  /*) ;;
  *) output="$(pwd)/$output" ;;
esac

if [ -e "$output" ]; then
  echo "error: refusing to overwrite existing artifact: $output" >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
  python_cmd=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
  python_cmd=python
else
  echo "error: python3 or python is required for the package-shape gate" >&2
  exit 3
fi

git -C "$repo_root" archive --format=zip --output="$output" HEAD:arc -- \
  main.py octos_stdio.py requirement_order.py acceptance.py guard.py \
  llm_proxy.py codegen.py package_shape.py hooks requirements.txt \
  arcbench_agent_runtime public-tests

shape_script="$script_dir/package_shape.py"
shape_archive="$output"
shape_output="${output%.zip}.shape.json"
if command -v cygpath >/dev/null 2>&1; then
  shape_script=$(cygpath -w "$shape_script")
  shape_archive=$(cygpath -w "$shape_archive")
  shape_output=$(cygpath -w "$shape_output")
fi
"$python_cmd" "$shape_script" agent --archive "$shape_archive" \
  --output "$shape_output" >/dev/null
echo "commit=$commit"
echo "artifact=$output"
shasum -a 256 "$output"
