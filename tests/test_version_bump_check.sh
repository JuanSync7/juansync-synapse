#!/usr/bin/env bash
# Tests for scripts/version-bump-check.sh
#
# Strategy: stub `git` on PATH so that classify_diff_against returns
# deterministic results. Each test case sets up a fixture directory with
# a stub `git` script, then invokes version-bump-check.sh with a fake
# BASE_REF and PR_LABELS env, and asserts exit code + output.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/version-bump-check.sh"

PASS=0
FAIL=0
FAILED_CASES=()

assert() {
    local name="$1"
    local expected_rc="$2"
    local actual_rc="$3"
    local stderr_log="${4:-}"
    local must_contain="${5:-}"

    if [ "$expected_rc" -eq "$actual_rc" ]; then
        if [ -n "$must_contain" ] && [ -n "$stderr_log" ]; then
            if grep -qF "$must_contain" "$stderr_log"; then
                echo "PASS  $name"
                PASS=$((PASS + 1))
                return
            fi
            echo "FAIL  $name (stderr did not contain '$must_contain')"
            cat "$stderr_log" >&2 || true
            FAIL=$((FAIL + 1))
            FAILED_CASES+=("$name")
            return
        fi
        echo "PASS  $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $name (expected rc=$expected_rc, got rc=$actual_rc)"
        [ -n "$stderr_log" ] && cat "$stderr_log" >&2 || true
        FAIL=$((FAIL + 1))
        FAILED_CASES+=("$name")
    fi
}

# Build a temp fixture: a directory with a stub `git` that emits a fixed
# `diff --name-status` for any args, plus a stub `python3` shim that runs
# real python3 against the real version_bump module. We don't actually need
# to stub python3 — we only need to control what `git diff` returns.
#
# Easiest: create a real tiny git repo with the right shape, and call the
# wrapper against it.

make_repo() {
    local dir="$1"
    local kind="$2"  # patch | minor | major

    mkdir -p "$dir"
    (
        cd "$dir"
        git init -q -b main
        git config user.email t@t
        git config user.name t

        # Initial commit
        echo "hi" > README.md
        mkdir -p synapse
        cat > synapse/SKILLS_REGISTRY.yaml <<'YAML'
version: 2
registry:
  - stage_name: design
    input_type: spec
    output_type: design_doc
YAML
        git add .
        git commit -q -m init

        case "$kind" in
            patch)
                echo "more docs" >> README.md
                git add . && git commit -q -m patch
                ;;
            minor)
                mkdir -p synapse/skills/new
                echo "# new" > synapse/skills/new/SKILL.md
                git add . && git commit -q -m minor
                ;;
            major)
                # Change output_type value
                sed -i 's/output_type: design_doc/output_type: design_artifact/' synapse/SKILLS_REGISTRY.yaml
                git add . && git commit -q -m major
                ;;
        esac
    )
}

run_case() {
    local name="$1"
    local kind="$2"
    local labels="$3"
    local expected_rc="$4"
    local must_contain="${5:-}"

    local tmp
    tmp="$(mktemp -d)"
    local repo="$tmp/repo"
    make_repo "$repo" "$kind"

    local stderr_log="$tmp/err.log"
    local rc=0
    (
        cd "$repo"
        BASE_REF="HEAD~1" PR_LABELS="$labels" "$SCRIPT"
    ) 2> "$stderr_log" || rc=$?

    assert "$name" "$expected_rc" "$rc" "$stderr_log" "$must_contain"
    rm -rf "$tmp"
}

# --- Cases ---
run_case "patch + bump:patch label → pass"   patch "bump:patch"           0
run_case "minor + bump:minor label → pass"   minor "bump:minor"           0
run_case "major + bump:major label → pass"   major "bump:major"           0
run_case "minor + bump:patch label → fail"   minor "bump:patch"           1 "expected bump:minor"
run_case "major + bump:minor label → fail"   major "bump:minor"           1 "expected bump:major"
run_case "patch + no bump label → fail"      patch ""                     1 "no bump:* label"
run_case "patch + multiple bump labels → fail" patch "bump:patch
bump:minor"                                                              1 "multiple bump"
run_case "extra non-bump labels are ignored" minor "needs-review
bump:minor
priority"                                                                0

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    printf 'Failed cases:\n'
    printf '  - %s\n' "${FAILED_CASES[@]}"
    exit 1
fi
exit 0
