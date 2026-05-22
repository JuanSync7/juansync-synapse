#!/usr/bin/env bash
# tag-stable.sh — promote the latest v<X>.<Y>.<Z>-pre.<N> tag to stable.
#
# Process:
#   1. Verify we are on `main` and the working tree is clean.
#   2. Find the latest v<X>.<Y>.<Z>-pre.<N> tag (highest version, highest N).
#   3. Create a new lightweight tag v<X>.<Y>.<Z> pointing to the same commit.
#   4. Push both the pre-tag and the new stable tag (unless DRY_RUN=1).
#
# Env:
#   DRY_RUN=1   Skip the actual tag creation and push (just print the plan).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$current_branch" != "main" ] && [ "${ALLOW_NON_MAIN:-0}" != "1" ]; then
    echo "ERROR: must be on 'main' to tag stable (current: $current_branch)" >&2
    echo "Set ALLOW_NON_MAIN=1 to override." >&2
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: working tree has uncommitted changes." >&2
    exit 1
fi

# Find latest pre-tag. `git tag --sort=-v:refname` orders by semver descending;
# pre-release suffixes sort under the same X.Y.Z so we just take the first match.
latest_pre="$(git tag --list 'v[0-9]*.[0-9]*.[0-9]*-pre.*' --sort=-v:refname | head -n1 || true)"

if [ -z "$latest_pre" ]; then
    echo "ERROR: no v*-pre.* tag found to promote." >&2
    exit 1
fi

# Strip the -pre.N suffix to get the stable tag name
stable_tag="${latest_pre%%-pre.*}"

# Resolve commit
target_sha="$(git rev-list -n1 "$latest_pre")"

if git rev-parse -q --verify "refs/tags/$stable_tag" >/dev/null; then
    echo "ERROR: stable tag $stable_tag already exists." >&2
    exit 1
fi

cat <<EOF
Promoting:
  pre-tag:    $latest_pre
  stable:     $stable_tag
  commit:     $target_sha
EOF

if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "(DRY_RUN=1 — skipping tag creation and push)"
    exit 0
fi

git tag "$stable_tag" "$target_sha"
git push origin "$stable_tag"
echo "Pushed $stable_tag → origin."
