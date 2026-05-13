#!/usr/bin/env bash
# Smoke-test scripts/lib/drift_cli.py end-to-end.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/drift_cli.py"
LOCK_CLI="python3 $REPO_ROOT/scripts/lib/lockfile_cli.py"

TMP="$(mktemp -d)"
FAKE_REPO="$TMP/fakerepo"
FAKE_HOME="$TMP/home"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# ---- fake repo with one artifact under synapse/skills/foo ----
mkdir -p "$FAKE_REPO/synapse/skills/foo"
cd "$FAKE_REPO"
git init -q -b main
git config user.email t@t
git config user.name "Test User"
printf "hello\nworld\n" > synapse/skills/foo/SKILL.md
git add .
git commit -q -m "init"
SHA="$(git rev-parse HEAD)"

# ---- project-scoped lockfile + pins ----
export SYNAPSE_PROJECT="$TMP"
export SYNAPSE_REPO_ROOT="$FAKE_REPO"
export HOME="$FAKE_HOME"
mkdir -p "$TMP/.synapse" "$FAKE_HOME"

LOCKFILE_PATH="$TMP/.synapse/installed.lock"

# Build a minimal lockfile by hand (lockfile_cli wants source path under repo).
HASH="$(python3 -c "
import sys, pathlib
sys.path.insert(0, '$REPO_ROOT/scripts/lib')
import hashing
print(hashing.hash_directory(pathlib.Path('$FAKE_REPO/synapse/skills/foo')))
")"

cat > "$LOCKFILE_PATH" <<EOF
schema_version = 1
synapse_repo = "$FAKE_REPO"
synapse_tag = ""
synapse_sha = "$SHA"
installed_at = "2026-05-06T00:00:00Z"
machine_id = "test"

[artifact."skill/foo"]
source_path = "synapse/skills/foo"
install_path = "$FAKE_HOME/.claude/skills/foo"
content_hash = "$HASH"
type = "skill"
status = "installed"
EOF

# 1. show — clean → exit 0
$CLI show skill/foo >/dev/null
echo "  ok   show clean"

# 2. introduce drift; show → exit 1
printf "hello\nuniverse\n" > synapse/skills/foo/SKILL.md
set +e; $CLI show skill/foo > "$TMP/show.out" 2> "$TMP/show.err"; rc=$?; set -e
[[ "$rc" == "1" ]] || { echo "FAIL: show should exit 1 with drift, got $rc"; cat "$TMP/show.err"; exit 1; }
grep -q "Drift in skill/foo" "$TMP/show.out" || { echo "FAIL: show missing header"; exit 1; }
grep -q "+universe" "$TMP/show.out" || { echo "FAIL: show missing diff"; exit 1; }
echo "  ok   show drift"

# 3. show --json
set +e; $CLI show skill/foo --json > "$TMP/show.json"; jrc=$?; set -e
[[ "$jrc" == "1" ]] || { echo "FAIL: show --json should exit 1, got $jrc"; exit 1; }
python3 -c "
import json
d = json.load(open('$TMP/show.json'))
assert d['key'] == 'skill/foo', d
assert any('+universe' in (f['diff'] or '') for f in d['files']), d
"
echo "  ok   show --json"

# 4. ignore
$CLI ignore skill/foo --reason "debug" --expires "2026-12-31" > "$TMP/ignore.out"
grep -q "Ignored drift in skill/foo until 2026-12-31" "$TMP/ignore.out"
python3 -c "
import tomllib
d = tomllib.loads(open('$TMP/.synapse/pins.toml').read())
assert 'skill/foo' in d['drift_exceptions'], d
assert d['drift_exceptions']['skill/foo']['expires'] == '2026-12-31', d
"
echo "  ok   ignore"

# 5. ignore without --expires emits warning
$CLI ignore skill/foo 2> "$TMP/ignore-warn.err" >/dev/null
grep -q "warn:" "$TMP/ignore-warn.err"
echo "  ok   ignore warns when no --expires"

# 6. adopt creates change_request
$CLI adopt skill/foo --slug "my fix" --reason "experimentation" > "$TMP/adopt.out"
grep -q "Adopted drift in skill/foo" "$TMP/adopt.out"
CR_FILE="$(ls $FAKE_REPO/synapse/skills/foo/change_requests/*.md | head -1)"
[[ -f "$CR_FILE" ]] || { echo "FAIL: CR not created"; exit 1; }
grep -q "title: my-fix" "$CR_FILE"
grep -q "author: test-user" "$CR_FILE"
grep -q "artifact: skill/foo" "$CR_FILE"
grep -q "+universe" "$CR_FILE"
# Source NOT restored
grep -q "universe" synapse/skills/foo/SKILL.md
echo "  ok   adopt"

# 7. stash
# Clean CR file so stash doesn't hit untracked-cleanup surprises (CR is in source_path)
rm -rf synapse/skills/foo/change_requests
$CLI stash skill/foo --reason "save my work" > "$TMP/stash.out"
STASH_DIR="$(ls -d $FAKE_HOME/.synapse/stash/*/ | head -1)"
[[ -d "$STASH_DIR" ]] || { echo "FAIL: stash dir not created"; exit 1; }
[[ -f "$STASH_DIR/STASH_META.toml" ]] || { echo "FAIL: STASH_META missing"; exit 1; }
[[ -f "$STASH_DIR/payload/SKILL.md" ]] || { echo "FAIL: payload missing"; exit 1; }
grep -q "universe" "$STASH_DIR/payload/SKILL.md"
# Source restored to canonical
grep -q "world" synapse/skills/foo/SKILL.md
! grep -q "universe" synapse/skills/foo/SKILL.md
echo "  ok   stash"

# 8. list-stashes
$CLI list-stashes --json > "$TMP/list.json"
python3 -c "
import json
arr = json.load(open('$TMP/list.json'))
assert len(arr) == 1, arr
assert arr[0]['artifact'] == 'skill/foo', arr
assert arr[0]['reason'] == 'save my work', arr
"
echo "  ok   list-stashes"

# 9. restore --yes
STASH_ID="$(basename $STASH_DIR)"
$CLI restore "$STASH_ID" --yes > "$TMP/restore.out"
grep -q "universe" synapse/skills/foo/SKILL.md
echo "  ok   restore --yes"

# 10. restore without --yes on non-tty fails
set +e
$CLI restore "$STASH_ID" </dev/null > "$TMP/r.out" 2> "$TMP/r.err"
rc=$?
set -e
[[ "$rc" == "1" ]] || { echo "FAIL: restore non-tty no --yes should exit 1, got $rc"; exit 1; }
echo "  ok   restore refuses non-tty without --yes"

# 11. ambiguous resolution: error path
# Add second artifact with same bare name
mkdir -p synapse/agents/foo
echo "agent" > synapse/agents/foo/AGENT.md
HASH2="$(python3 -c "
import sys, pathlib
sys.path.insert(0, '$REPO_ROOT/scripts/lib')
import hashing
print(hashing.hash_directory(pathlib.Path('$FAKE_REPO/synapse/agents/foo')))
")"
cat >> "$LOCKFILE_PATH" <<EOF

[artifact."agent/foo"]
source_path = "synapse/agents/foo"
install_path = "$FAKE_HOME/.claude/agents/foo"
content_hash = "$HASH2"
type = "agent"
status = "installed"
EOF
set +e
$CLI show foo > "$TMP/amb.out" 2> "$TMP/amb.err"
rc=$?
set -e
[[ "$rc" == "2" ]] || { echo "FAIL: ambiguous should exit 2, got $rc"; exit 1; }
grep -q "ambiguous" "$TMP/amb.err"
echo "  ok   ambiguous bare name rejected"

echo "drift_cli: all subcommands ok"
