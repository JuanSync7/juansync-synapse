#!/usr/bin/env bash
# tag-dev.sh — local convenience: classify the current branch's diff
# against main, then PRINT (not apply) the next pre-tag.
#
# Does NOT push, does NOT create the tag. Pure dry run.
#
# Inputs (env, optional):
#   BASE_REF   default: main
#   HEAD_REF   default: HEAD
set -euo pipefail

BASE_REF="${BASE_REF:-main}"
HEAD_REF="${HEAD_REF:-HEAD}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# Classify the diff
classification="$(
    PYTHONPATH="$LIB_DIR" \
    BASE_REF="$BASE_REF" \
    HEAD_REF="$HEAD_REF" \
    REPO_ROOT="$REPO_ROOT" \
    python3 -c "
import os, version_bump
print(version_bump.classify_diff_against(
    os.environ['BASE_REF'],
    os.environ['HEAD_REF'],
    os.environ['REPO_ROOT'],
))
"
)"

# Find the latest *stable* tag (v<X>.<Y>.<Z> with no -pre suffix).
# We bump from the stable line; pre-tags only contribute to the N counter.
latest_stable="$(
    git -C "$REPO_ROOT" tag --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname \
        | grep -v -- '-' | head -n1 || true
)"

if [ -z "$latest_stable" ]; then
    base_major=0
    base_minor=0
    base_patch=0
else
    stripped="${latest_stable#v}"
    IFS='.' read -r base_major base_minor base_patch <<< "$stripped"
fi
latest="$latest_stable"

case "$classification" in
    major) next_major=$((base_major + 1)); next_minor=0;                next_patch=0 ;;
    minor) next_major=$base_major;          next_minor=$((base_minor+1)); next_patch=0 ;;
    patch) next_major=$base_major;          next_minor=$base_minor;     next_patch=$((base_patch+1)) ;;
    *) echo "ERROR: unknown classification: $classification" >&2; exit 2 ;;
esac

base_version="v${next_major}.${next_minor}.${next_patch}"

# Find the highest existing N for this version's pre-tags; next is +1.
highest_n="$(
    git -C "$REPO_ROOT" tag --list "${base_version}-pre.*" \
        | sed -n "s/^${base_version}-pre\.\([0-9][0-9]*\)$/\1/p" \
        | sort -n | tail -n1
)"
next_n=$(( ${highest_n:-0} + 1 ))

next_tag="${base_version}-pre.${next_n}"

cat <<EOF
Diff classification: $classification
Latest tag:          ${latest:-<none>}
Next pre-tag:        $next_tag
(dry run — nothing applied)
EOF
