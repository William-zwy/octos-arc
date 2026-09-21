#!/bin/sh
# Build a commit-bound, content-addressed ARC platform Agent ZIP.
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
requested_output=${1:-}
if [ -n "$requested_output" ]; then
  case "$requested_output" in
    /*) output="$requested_output" ;;
    *) output="$(pwd)/$requested_output" ;;
  esac
else
  output=""
fi

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
  python_cmd=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
  python_cmd=python
else
  echo "error: python3 or python is required for the package-shape gate" >&2
  exit 3
fi

temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/octos-arc-pack.XXXXXX")
temp_archive="$temp_dir/agent.zip"
cleanup() {
  rm -f -- "$temp_archive"
  rmdir -- "$temp_dir" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM

git -c core.autocrlf=false -C "$repo_root" archive --format=zip --output="$temp_archive" HEAD:arc -- \
  main.py octos_stdio.py requirement_order.py acceptance.py guard.py \
  llm_proxy.py codegen.py build_identity.py package_shape.py hooks requirements.txt \
  arcbench_agent_runtime public-tests

identity_script="$script_dir/build_identity.py"
shape_script="$script_dir/package_shape.py"
identity_archive="$temp_archive"
if command -v cygpath >/dev/null 2>&1; then
  identity_script=$(cygpath -w "$identity_script")
  identity_archive=$(cygpath -w "$identity_archive")
fi
"$python_cmd" "$identity_script" embed --archive "$identity_archive" \
  --commit "$commit" >/dev/null
archive_sha256=$("$python_cmd" -c \
  'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest().upper())' \
  "$identity_archive")
sha12=$("$python_cmd" -c 'import sys; print(sys.argv[1][:12].lower())' "$archive_sha256")

if [ -z "$output" ]; then
  release_dir="$script_dir/releases"
  mkdir -p -- "$release_dir"
  output="$release_dir/octos-arc-agent-${short_commit}-${sha12}.zip"
fi
shape_output="${output%.zip}.shape.json"
release_output="${output%.zip}.release.json"
checksum_output="${output}.sha256"
for destination in "$output" "$shape_output" "$release_output" "$checksum_output"; do
  if [ -e "$destination" ]; then
    echo "error: refusing to overwrite existing artifact: $destination" >&2
    exit 2
  fi
done
mv -- "$temp_archive" "$output"

shape_archive="$output"
shape_script_native="$shape_script"
shape_output_native="$shape_output"
identity_script_native="$identity_script"
release_output_native="$release_output"
checksum_output_native="$checksum_output"
if command -v cygpath >/dev/null 2>&1; then
  shape_script_native=$(cygpath -w "$shape_script")
  shape_archive=$(cygpath -w "$shape_archive")
  shape_output_native=$(cygpath -w "$shape_output")
  identity_script_native=$(cygpath -w "$script_dir/build_identity.py")
  release_output_native=$(cygpath -w "$release_output")
  checksum_output_native=$(cygpath -w "$checksum_output")
fi
"$python_cmd" "$shape_script_native" agent --archive "$shape_archive" \
  --output "$shape_output_native" >/dev/null
"$python_cmd" "$identity_script_native" release --archive "$shape_archive" \
  --shape "$shape_output_native" --output "$release_output_native" \
  --checksum "$checksum_output_native" >/dev/null
build_id=$("$python_cmd" "$identity_script_native" inspect --archive "$shape_archive" \
  --field build_id)
echo "commit=$commit"
echo "artifact=$output"
echo "sha256=$archive_sha256"
echo "build_id=$build_id"
echo "release_manifest=$release_output"
echo "shape_manifest=$shape_output"
echo "checksum=$checksum_output"
