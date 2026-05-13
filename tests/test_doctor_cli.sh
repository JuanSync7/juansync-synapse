#!/usr/bin/env bash
# Smoke-test scripts/lib/doctor_cli.py end-to-end.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/doctor_cli.py"

TMP="$(mktemp -d)"
FAKE_REPO="$TMP/fakerepo"
INSTALL_ROOT="$TMP/install"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

mkdir -p "$FAKE_REPO/synapse/skills/foo"
git -C "$FAKE_REPO" init -q -b main
git -C "$FAKE_REPO" config user.email t@t
git -C "$FAKE_REPO" config user.name t
echo "body" > "$FAKE_REPO/synapse/skills/foo/SKILL.md"
git -C "$FAKE_REPO" add .
git -C "$FAKE_REPO" commit -q -m c1
HEAD_SHA=$(git -C "$FAKE_REPO" rev-parse HEAD)

mkdir -p "$INSTALL_ROOT/foo"
echo "body" > "$INSTALL_ROOT/foo/SKILL.md"

# Compute hash via the same hashing module
HASH=$(python3 -c "
import sys, pathlib
sys.path.insert(0, '$REPO_ROOT/scripts/lib')
import hashing
print(hashing.hash_directory(pathlib.Path('$FAKE_REPO/synapse/skills/foo')))
")

export SYNAPSE_PROJECT="$TMP"
export SYNAPSE_REPO_ROOT="$FAKE_REPO"
mkdir -p "$TMP/.synapse"

# Write a valid lockfile manually
cat > "$TMP/.synapse/installed.lock" <<EOF
schema_version = 1
synapse_repo = "$FAKE_REPO"
synapse_tag = ""
synapse_sha = "$HEAD_SHA"
installed_at = "2026-05-06T00:00:00Z"
machine_id = "test"

[artifact."skill/foo"]
source_path = "synapse/skills/foo"
install_path = "$INSTALL_ROOT/foo"
content_hash = "$HASH"
type = "skill"
status = "installed"
EOF

# Pin to main so stale/pin_rot are inactive
cat > "$TMP/.synapse/pins.toml" <<EOF
schema_version = 1

[synapse]
pin = "main"
EOF

# 1. clean → exit 0
set +e
OUT=$($CLI --skip submodule_stale 2>&1)
RC=$?
set -e
[[ $RC -eq 0 ]] || { echo "FAIL: clean expected exit 0, got $RC"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -qi "no findings\|0 errors, 0 warnings" || {
    echo "FAIL: clean expected 'no findings', got: $OUT"; exit 1; }
echo "  ok   clean repo → exit 0"

# 2. drift → exit 1
echo "modified" > "$FAKE_REPO/synapse/skills/foo/SKILL.md"
set +e
OUT=$($CLI --skip submodule_stale 2>&1)
RC=$?
set -e
[[ $RC -eq 1 ]] || { echo "FAIL: drift expected exit 1, got $RC"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -q "drift" || { echo "FAIL: missing 'drift' in output"; echo "$OUT"; exit 1; }
echo "  ok   drift → exit 1"

# 3. missing (also still drifted) → exit 2
rm -rf "$INSTALL_ROOT/foo"
set +e
OUT=$($CLI --skip submodule_stale 2>&1)
RC=$?
set -e
[[ $RC -eq 2 ]] || { echo "FAIL: missing expected exit 2, got $RC"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -q "missing" || { echo "FAIL: missing 'missing' in output"; echo "$OUT"; exit 1; }
echo "  ok   missing → exit 2"

# Restore for JSON test
mkdir -p "$INSTALL_ROOT/foo"
echo "modified" > "$INSTALL_ROOT/foo/SKILL.md"

# 4. --json produces parseable JSON
set +e
OUT=$($CLI --json --skip submodule_stale 2>&1)
RC=$?
set -e
echo "$OUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'findings' in d
assert 'summary' in d
assert 'exit_code' in d
" || { echo "FAIL: bad JSON: $OUT"; exit 1; }
echo "  ok   --json parseable"

# 5. --skip drift,submodule_stale → fewer findings
set +e
OUT=$($CLI --json --skip drift,submodule_stale 2>&1)
set -e
echo "$OUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for f in d['findings']:
    assert f['category'] != 'drift', 'drift should be skipped'
    assert f['category'] != 'submodule_stale', 'submodule_stale should be skipped'
"
echo "  ok   --skip filters categories"

# 6. --severity-floor warn drops info findings
# Restore clean state
echo "body" > "$FAKE_REPO/synapse/skills/foo/SKILL.md"
echo "body" > "$INSTALL_ROOT/foo/SKILL.md"
# Add an external entry that will produce only an info finding via network failure
cat >> "$TMP/.synapse/installed.lock" <<EOF

[external."some-suite"]
submodule_path = "external/some-suite"
submodule_sha = "$(printf 'a%.0s' {1..40})"
content_hash = "sha256:$(printf '0%.0s' {1..64})"
status = "installed"
EOF
set +e
OUT=$($CLI --severity-floor warn 2>&1)
RC=$?
set -e
[[ $RC -eq 0 ]] || { echo "FAIL: floor=warn with only info expected exit 0, got $RC"; echo "$OUT"; exit 1; }
echo "  ok   --severity-floor warn drops info"

echo ""
echo "All doctor_cli smoke tests passed."
