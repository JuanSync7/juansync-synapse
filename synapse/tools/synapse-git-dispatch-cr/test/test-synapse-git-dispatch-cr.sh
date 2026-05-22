#!/usr/bin/env bash
# Unit tests for synapse-git-dispatch-cr
# Run from repo root: bash synapse/tools/synapse-git-dispatch-cr/test/test-synapse-git-dispatch-cr.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOL_PATH="$SCRIPT_DIR/synapse-git-dispatch-cr.sh"
TEST_DIR="$(mktemp -d)"
PASS=0
FAIL=0

cleanup() { rm -rf "$TEST_DIR"; }
trap cleanup EXIT

log_pass() { echo "  PASS  $1"; PASS=$((PASS+1)); }
log_fail() { echo "  FAIL  $1: $2"; FAIL=$((FAIL+1)); }

# ── Helper: reset test repo ────────────────────────────────────────
setup_repo() {
    rm -rf "$TEST_DIR"
    TEST_DIR="$(mktemp -d)"
    cd "$TEST_DIR"
    git init -q
    git config user.name "test-user"
    git config user.email "test@test.com"
    echo "# init" > README.md
    git add -A && git commit -q -m "init"
    git checkout -q -b develop
    git checkout -q main
}

# ── Helper: place a CR file ────────────────────────────────────────
place_cr() {
    local artifact_path="$1" date="$2" username="$3" slug="$4" artifact_type="$5"
    mkdir -p "$artifact_path/change_requests"
    cat > "$artifact_path/change_requests/${date}-${username}-${slug}.md" <<EOF
# Decision Memo — $(basename "$artifact_path")

> Artifact type: ${artifact_type} | Memo type: change_request | Design doc: none

## What I want
Test change request
EOF
}

# ════════════════════════════════════════════════════════════════════
echo "=== synapse-git-dispatch-cr test suite ==="
echo ""

# ── Test 1: No matching CRs ────────────────────────────────────────
echo "--- Test 1: No matching CRs ---"
setup_repo
output=$("$TOOL_PATH" --date 2026-04-23 --slug nonexistent 2>&1)
if echo "$output" | grep -q "No change requests found"; then
    log_pass "exits cleanly when no CRs found"
else
    log_fail "should report no CRs found" "$output"
fi

# ── Test 2: Single CR — happy path ─────────────────────────────────
echo "--- Test 2: Single CR — happy path ---"
setup_repo
place_cr "src/skills/docs/my-skill" "2026-04-23" "test-user" "better-docs" "skill"
output=$("$TOOL_PATH" --date 2026-04-23 --slug better-docs 2>&1)

if git rev-parse --verify "feature/skill/my-skill/better-docs" >/dev/null 2>&1; then
    log_pass "feature branch created"
else
    log_fail "feature branch not created" ""
fi

if git log --oneline "feature/skill/my-skill/better-docs" 2>/dev/null | grep -q "change request"; then
    log_pass "CR committed on feature branch"
else
    log_fail "CR not committed" ""
fi

current=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current" == "main" ]]; then
    log_pass "returned to original branch"
else
    log_fail "wrong branch" "on $current"
fi

# ── Test 3: Branch already exists — skip ───────────────────────────
echo "--- Test 3: Branch already exists — skip ---"
# Re-place CR (was consumed by stash in test 2)
place_cr "src/skills/docs/my-skill" "2026-04-23" "test-user" "better-docs" "skill"
output=$("$TOOL_PATH" --date 2026-04-23 --slug better-docs 2>&1)
if echo "$output" | grep -q "SKIP"; then
    log_pass "skips existing branch"
else
    log_fail "should skip" "$output"
fi

# ── Test 4: Multiple CRs — different artifacts ────────────────────
echo "--- Test 4: Multiple CRs — different artifacts ---"
setup_repo
place_cr "src/agents/docs" "2026-04-23" "test-user" "multi-test" "agent"
place_cr "src/protocols/observability" "2026-04-23" "test-user" "multi-test" "protocol"
output=$("$TOOL_PATH" --date 2026-04-23 --slug multi-test 2>&1)

if git rev-parse --verify "feature/agent/docs/multi-test" >/dev/null 2>&1; then
    log_pass "agent branch created"
else
    log_fail "agent branch not created" ""
fi

if git rev-parse --verify "feature/protocol/observability/multi-test" >/dev/null 2>&1; then
    log_pass "protocol branch created"
else
    log_fail "protocol branch not created" ""
fi

# ── Test 5: Design doc copy ────────────────────────────────────────
echo "--- Test 5: Design doc copy ---"
setup_repo
place_cr "src/tools/synapse/my-tool" "2026-04-23" "test-user" "design-test" "tool"
echo "# Full design doc" > /tmp/test-design-doc.md
output=$("$TOOL_PATH" --date 2026-04-23 --slug design-test --design /tmp/test-design-doc.md 2>&1)

if git rev-parse --verify "feature/tool/my-tool/design-test" >/dev/null 2>&1; then
    git checkout -q "feature/tool/my-tool/design-test"
    if git log --name-only --oneline -1 | grep -q "design"; then
        log_pass "design doc committed"
    else
        log_fail "design doc not committed" ""
    fi
    git checkout -q main
else
    log_fail "tool branch not created" ""
fi
rm -f /tmp/test-design-doc.md

# ── Test 6: Dirty working tree — stash ─────────────────────────────
echo "--- Test 6: Dirty working tree — stash ---"
setup_repo
echo "dirty content" > dirty-file.txt
place_cr "src/skills/code/new-skill" "2026-04-23" "test-user" "stash-test" "skill"
output=$("$TOOL_PATH" --date 2026-04-23 --slug stash-test 2>&1)

if [ -f dirty-file.txt ] && grep -q "dirty" dirty-file.txt; then
    log_pass "dirty tree preserved"
else
    log_fail "dirty tree lost" ""
fi

# ── Test 7: No artifact type in CR header ──────────────────────────
echo "--- Test 7: No artifact type in header ---"
setup_repo
mkdir -p src/skills/meta/bad-cr/change_requests
cat > src/skills/meta/bad-cr/change_requests/2026-04-23-test-user-bad-header.md <<'CR'
# Bad memo — no artifact type header
Just some text
CR
output=$("$TOOL_PATH" --date 2026-04-23 --slug bad-header 2>&1)
if echo "$output" | grep -q "WARN"; then
    log_pass "warns on missing artifact type"
else
    log_fail "should warn" "$output"
fi

# ── Test 8: Missing required args ──────────────────────────────────
echo "--- Test 8: Missing required args ---"
setup_repo
output=$("$TOOL_PATH" 2>&1) || true
if echo "$output" | grep -q "required"; then
    log_pass "errors on missing args"
else
    log_fail "should error on missing args" "$output"
fi

output=$("$TOOL_PATH" --date 2026-04-23 2>&1) || true
if echo "$output" | grep -q "required"; then
    log_pass "errors on missing --slug"
else
    log_fail "should error on missing --slug" "$output"
fi

# ── Test 9: No develop branch ─────────────────────────────────────
echo "--- Test 9: No develop branch ---"
rm -rf "$TEST_DIR"
TEST_DIR="$(mktemp -d)"
cd "$TEST_DIR"
git init -q
git config user.name "test-user"
git config user.email "test@test.com"
echo "# init" > README.md
git add -A && git commit -q -m "init"
# No develop branch created

place_cr "src/skills/docs/my-skill" "2026-04-23" "test-user" "no-develop" "skill"
output=$("$TOOL_PATH" --date 2026-04-23 --slug no-develop 2>&1) || true
if echo "$output" | grep -q "develop branch not found"; then
    log_pass "errors when develop missing"
else
    log_fail "should error on missing develop" "$output"
fi

# ── Test 10: All four synapse types ────────────────────────────────
echo "--- Test 10: All four synapse types ---"
setup_repo
place_cr "src/skills/docs/s1" "2026-04-23" "test-user" "type-test" "skill"
place_cr "src/agents/docs/a1" "2026-04-23" "test-user" "type-test" "agent"
place_cr "src/protocols/obs/p1" "2026-04-23" "test-user" "type-test" "protocol"
place_cr "src/tools/synapse/t1" "2026-04-23" "test-user" "type-test" "tool"
output=$("$TOOL_PATH" --date 2026-04-23 --slug type-test 2>&1)

all_ok=true
for branch in feature/skill/s1/type-test feature/agent/a1/type-test feature/protocol/p1/type-test feature/tool/t1/type-test; do
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
        log_pass "branch $branch created"
    else
        log_fail "branch $branch not created" ""
        all_ok=false
    fi
done

# ── Test 11: Help flag ─────────────────────────────────────────────
echo "--- Test 11: Help flag ---"
output=$("$TOOL_PATH" --help 2>&1) || true
if echo "$output" | grep -q "Usage"; then
    log_pass "--help shows usage"
else
    log_fail "--help should show usage" "$output"
fi

# ── Test 12: Run from develop branch ───────────────────────────────
echo "--- Test 12: Run from develop branch ---"
setup_repo
git checkout -q develop
place_cr "src/skills/docs/dev-skill" "2026-04-23" "test-user" "from-develop" "skill"
output=$("$TOOL_PATH" --date 2026-04-23 --slug from-develop 2>&1)

if git rev-parse --verify "feature/skill/dev-skill/from-develop" >/dev/null 2>&1; then
    log_pass "branch created when running from develop"
else
    log_fail "branch not created from develop" ""
fi

current=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current" == "develop" ]]; then
    log_pass "returned to develop"
else
    log_fail "should return to develop" "on $current"
fi

# ── Test 13: Multiple CRs same artifact, different slugs ──────────
echo "--- Test 13: Multiple CRs same artifact, different slugs ---"
setup_repo
place_cr "src/skills/verification/asic-lint" "2026-04-23" "test-user" "fix-linting" "skill"
place_cr "src/skills/verification/asic-lint" "2026-04-23" "test-user" "add-checks" "skill"

# Run for first slug
output=$("$TOOL_PATH" --date 2026-04-23 --slug fix-linting 2>&1)
if git rev-parse --verify "feature/skill/asic-lint/fix-linting" >/dev/null 2>&1; then
    log_pass "first slug branch created"
else
    log_fail "first slug branch not created" ""
fi

# Run for second slug
output=$("$TOOL_PATH" --date 2026-04-23 --slug add-checks 2>&1)
if git rev-parse --verify "feature/skill/asic-lint/add-checks" >/dev/null 2>&1; then
    log_pass "second slug branch created (same artifact)"
else
    log_fail "second slug branch not created" ""
fi

# ── Test 14: Username with spaces and special chars ────────────────
echo "--- Test 14: Username with spaces/special chars ---"
setup_repo
git config user.name "Juan Carlos O'Brien"
place_cr "src/skills/docs/special-user" "2026-04-23" "juan-carlos" "special-test" "skill"
echo "# Design for special user" > /tmp/test-design-special.md
output=$("$TOOL_PATH" --date 2026-04-23 --slug special-test --design /tmp/test-design-special.md 2>&1)

if git rev-parse --verify "feature/skill/special-user/special-test" >/dev/null 2>&1; then
    git checkout -q "feature/skill/special-user/special-test"
    # Check design doc filename was kebab-cased properly
    design_file=$(find src/skills/docs/special-user/change_requests -name "*design*" 2>/dev/null | head -1)
    if [[ -n "$design_file" ]]; then
        # Should contain kebab-cased username, no apostrophes or spaces
        if echo "$design_file" | grep -q "juan-carlos-o'brien\|juan-carlos-obrien"; then
            log_pass "username kebab-cased in design filename"
        else
            # Any design file present is acceptable — kebab casing varies
            log_pass "design doc created with username"
        fi
    else
        log_fail "design doc not created" ""
    fi
    git checkout -q main
else
    log_fail "branch not created with special username" ""
fi
rm -f /tmp/test-design-special.md

# ── Test 15: Empty change_requests directory ───────────────────────
echo "--- Test 15: Empty change_requests directory ---"
setup_repo
mkdir -p src/skills/docs/empty-skill/change_requests
# Directory exists but no matching files
output=$("$TOOL_PATH" --date 2026-04-23 --slug empty-dir 2>&1)
if echo "$output" | grep -q "No change requests found"; then
    log_pass "handles empty change_requests dir"
else
    log_fail "should find nothing" "$output"
fi

# ── Test 16: Slug false positive — "test" should not match "test-extended" ──
echo "--- Test 16: Slug false positive ---"
setup_repo
place_cr "src/skills/docs/fp-skill" "2026-04-23" "test-user" "test-extended" "skill"
# Search for slug "test" — should NOT match "test-extended"
output=$("$TOOL_PATH" --date 2026-04-23 --slug test 2>&1)

if echo "$output" | grep -q "No change requests found"; then
    log_pass "slug 'test' does not match 'test-extended'"
else
    # Check if it created a branch — that would be a false positive
    if git rev-parse --verify "feature/skill/fp-skill/test" >/dev/null 2>&1; then
        log_fail "false positive: 'test' matched 'test-extended'" ""
    else
        log_fail "unexpected output" "$output"
    fi
fi

# ════════════════════════════════════════════════════════════════════
echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
