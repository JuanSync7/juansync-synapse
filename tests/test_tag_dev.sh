#!/usr/bin/env bash
# Smoke test for scripts/tag-dev.sh — dry-run only, no real tagging.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/tag-dev.sh"

PASS=0
FAIL=0

run_case() {
    local name="$1"
    local kind="$2"          # patch|minor|major
    local existing_tag="$3"  # e.g. v0.1.0  or empty
    local existing_pre="$4"  # e.g. v0.2.0-pre.1  or empty
    local must_contain="$5"

    local tmp; tmp="$(mktemp -d)"
    local repo="$tmp/repo"
    mkdir -p "$repo"
    (
        cd "$repo"
        git init -q -b main
        git config user.email t@t
        git config user.name t
        echo init > README.md
        mkdir -p synapse
        cat > synapse/SKILLS_REGISTRY.yaml <<'YAML'
version: 2
registry:
  - stage_name: design
    input_type: spec
    output_type: design_doc
YAML
        git add . && git commit -q -m init

        [ -n "$existing_tag" ] && git tag "$existing_tag"
        [ -n "$existing_pre" ] && git tag "$existing_pre"

        case "$kind" in
            patch) echo more >> README.md ;;
            minor) mkdir -p synapse/skills/x && echo "# new" > synapse/skills/x/SKILL.md ;;
            major) sed -i 's/output_type: design_doc/output_type: design_artifact/' synapse/SKILLS_REGISTRY.yaml ;;
        esac
        git add . && git commit -q -m change
    )

    local out rc=0
    out="$(BASE_REF=HEAD~1 HEAD_REF=HEAD bash -c "cd '$repo' && '$SCRIPT'" 2>&1)" || rc=$?

    if [ "$rc" -eq 0 ] && grep -qF "$must_contain" <<< "$out"; then
        echo "PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $name (rc=$rc, expected to contain '$must_contain')"
        echo "$out" >&2
        FAIL=$((FAIL + 1))
    fi
    rm -rf "$tmp"
}

# No prior tag, patch diff → v0.0.1-pre.1
run_case "no-prior-tag patch"  patch ""        ""              "v0.0.1-pre.1"
# Prior v1.2.3 stable, minor diff → v1.3.0-pre.1
run_case "prior-stable minor"  minor "v1.2.3"  ""              "v1.3.0-pre.1"
# Prior v1.2.3 stable, major diff → v2.0.0-pre.1
run_case "prior-stable major"  major "v1.2.3"  ""              "v2.0.0-pre.1"
# Prior pre-tags exist for the target version → next N increments
run_case "increment N"         minor "v1.2.3"  "v1.3.0-pre.2"  "v1.3.0-pre.3"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
