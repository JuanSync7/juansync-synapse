#!/usr/bin/env bash
# version-bump-check.sh — CI gate that asserts a PR's bump label matches
# the mechanical classification of its diff.
#
# Inputs (env):
#   BASE_REF    Required. Git ref to diff against (e.g. origin/main).
#   PR_LABELS   Required. Newline-separated GitHub PR labels.
#   HEAD_REF    Optional. Defaults to HEAD.
#
# Exit codes:
#   0  label matches diff classification
#   1  mismatch, missing label, or multiple bump:* labels
#   2  invocation error (missing BASE_REF, etc.)
set -euo pipefail

if [ -z "${BASE_REF:-}" ]; then
    echo "ERROR: BASE_REF env var is required" >&2
    exit 2
fi

HEAD_REF="${HEAD_REF:-HEAD}"
PR_LABELS="${PR_LABELS:-}"

# The wrapper itself ships from ai-synapse, so locate the python module
# relative to this script — not relative to the cwd's git repo (which may
# be a downstream repo or a test fixture).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
# Diff repo defaults to cwd (where the PR's checkout lives).
DIFF_REPO="${DIFF_REPO:-$(pwd)}"

# Compute classification by invoking the python module.
classification="$(
    PYTHONPATH="$LIB_DIR" DIFF_REPO="$DIFF_REPO" python3 -c "
import os
import version_bump
print(version_bump.classify_diff_against(
    os.environ['BASE_REF'],
    os.environ.get('HEAD_REF', 'HEAD'),
    os.environ['DIFF_REPO'],
))
"
)"

# Extract bump:* labels (one per line, trimmed)
bump_labels=()
while IFS= read -r line; do
    # strip whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    case "$line" in
        bump:major|bump:minor|bump:patch) bump_labels+=("$line") ;;
    esac
done <<< "$PR_LABELS"

if [ "${#bump_labels[@]}" -eq 0 ]; then
    echo "ERROR: PR has no bump:* label." >&2
    echo "Diff classifies as '$classification'. Add a 'bump:$classification' label." >&2
    exit 1
fi

if [ "${#bump_labels[@]}" -gt 1 ]; then
    echo "ERROR: PR has multiple bump:* labels: ${bump_labels[*]}" >&2
    echo "Exactly one bump:major / bump:minor / bump:patch label is required." >&2
    exit 1
fi

label="${bump_labels[0]}"
expected="bump:$classification"

if [ "$label" = "$expected" ]; then
    echo "OK: diff classifies as '$classification', label '$label' matches."
    exit 0
fi

cat >&2 <<EOF
ERROR: bump label mismatch.
  Diff classifies as: $classification (expected $expected)
  PR has label:       $label

Either change the bump label to '$expected' or revise the change so its
classification matches the intended label.
EOF
exit 1
