#!/usr/bin/env bash
# Smoke-test scripts/lib/clerk_cli.py.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/clerk_cli.py"

TMP="$(mktemp -d)"
FAKE_HOME="$TMP/home"
FAKE_REPO="$TMP/repo"
mkdir -p "$FAKE_HOME" "$FAKE_REPO"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export HOME="$FAKE_HOME"
export SYNAPSE_REPO_ROOT="$FAKE_REPO"

# Initialize a minimal repo with no .gitmodules.
cd "$FAKE_REPO"
git init -q -b main
git config user.email t@t
git config user.name "T"
echo "x" > x.txt
git add x.txt
git commit -q -m "init"

echo "==> clerk status (no state) — should report 'no clerk activity yet'"
out="$($CLI status)"
if ! grep -q "no clerk activity yet" <<<"$out"; then
    echo "FAIL: expected 'no clerk activity yet'"
    echo "got: $out"
    exit 1
fi
echo "ok"

echo ""
echo "==> clerk status --json"
out="$($CLI status --json)"
if ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); assert d['submodules']=={}" "$out"; then
    echo "FAIL: bad json output"
    echo "$out"
    exit 1
fi
echo "ok"

echo ""
echo "==> clerk doctor (no .gitmodules) — must not crash"
$CLI doctor >/dev/null
echo "ok"

echo ""
echo "==> clerk bump-externals (no submodules) — should print 'No external/ submodules'"
out="$($CLI bump-externals)"
if ! grep -q "No external/ submodules" <<<"$out"; then
    echo "FAIL: expected 'No external/ submodules'"
    echo "got: $out"
    exit 1
fi
echo "ok"

# Now register a fake submodule pointing at a local upstream repo,
# so ls-remote works without network.
UPSTREAM="$TMP/upstream"
mkdir -p "$UPSTREAM"
cd "$UPSTREAM"
git init -q -b main
git config user.email t@t
git config user.name "T"
echo "y" > y.txt
git add y.txt
git commit -q -m "init"
git tag v1.0.0
git tag v0.9.0-pre.1   # not stable; should be filtered

# Add a submodule clone inside the fake repo (doesn't need to be initialized;
# clerk reads .gitmodules + ls-remote).
cd "$FAKE_REPO"
mkdir -p external/foo
cat > .gitmodules <<EOF
[submodule "foo"]
    path = external/foo
    url = $UPSTREAM
EOF
git add .gitmodules
git commit -q -m "register submodule"

echo ""
echo "==> clerk bump-externals (dry-run) against local upstream"
out="$($CLI bump-externals 2>&1)"
echo "$out"
# Expect either BUMP or up-to-date depending on whether submodule SHA matches.
# We never initialized the submodule so current_sha is empty → BUMP expected.
if ! grep -qE "BUMP|up-to-date" <<<"$out"; then
    echo "FAIL: expected a BUMP or up-to-date row"
    exit 1
fi
if ! grep -q "v1.0.0" <<<"$out"; then
    echo "FAIL: expected target tag v1.0.0 in plan"
    exit 1
fi
if ! grep -q "Dry-run only" <<<"$out"; then
    echo "FAIL: expected dry-run footer"
    exit 1
fi
echo "ok"

echo ""
echo "==> clerk bump-externals --json"
out="$($CLI bump-externals --json)"
python3 -c "
import json, sys
d = json.loads(sys.argv[1])
assert 'plans' in d, 'missing plans key'
assert d['apply'] is False, 'expected dry-run'
assert len(d['plans']) == 1
p = d['plans'][0]
assert p['submodule_path'] == 'external/foo'
assert p['target_tag'] == 'v1.0.0'
" "$out"
echo "ok"

echo ""
echo "==> clerk status (after dry-run recorded seen_tag)"
out="$($CLI status)"
if ! grep -q "external/foo" <<<"$out"; then
    echo "FAIL: expected external/foo in status"
    echo "$out"
    exit 1
fi
if ! grep -q "v1.0.0" <<<"$out"; then
    echo "FAIL: expected v1.0.0 seen-tag in status"
    echo "$out"
    exit 1
fi
echo "ok"

echo ""
echo "All clerk CLI smoke tests passed."
