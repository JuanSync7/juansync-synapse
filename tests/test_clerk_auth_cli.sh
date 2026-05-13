#!/usr/bin/env bash
# Smoke-test scripts/lib/clerk_cli.py for the new `auth` subcommand + doctor reporting.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/clerk_cli.py"

TMP="$(mktemp -d)"
FAKE_HOME="$TMP/home"
FAKE_REPO="$TMP/repo"
mkdir -p "$FAKE_HOME/.synapse" "$FAKE_REPO"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export HOME="$FAKE_HOME"
export SYNAPSE_REPO_ROOT="$FAKE_REPO"
unset SYNAPSE_CLERK_TOKEN || true
unset CLERK_APP_TOK || true

cd "$FAKE_REPO"
git init -q -b main
git config user.email t@t
git config user.name "T"
echo "x" > x.txt
git add x.txt
git commit -q -m "init"

echo "==> clerk auth show (no config) — defaults to PAT mode"
out="$($CLI auth show)"
echo "$out"
if ! grep -q "auth.*pat" <<<"$out"; then
    echo "FAIL: expected default mode 'pat'"; exit 1
fi
if ! grep -q "SYNAPSE_CLERK_TOKEN" <<<"$out"; then
    echo "FAIL: expected default token_env name"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk auth show --json"
out="$($CLI auth show --json)"
python3 -c "
import json, sys
d = json.loads(sys.argv[1])
assert d['auth'] == 'pat', d
assert d['pat']['token_env'] == 'SYNAPSE_CLERK_TOKEN'
assert d.get('app') in (None, {})
" "$out"
echo "ok"

echo ""
echo "==> clerk auth set-mode app (writes app block placeholder, then pat)"
# set-mode app needs at minimum app_id/installation_id/private_key_path; supply via flags
KEY="$TMP/k.pem"
openssl genrsa -out "$KEY" 2048 >/dev/null 2>&1
$CLI auth set-mode app --app-id 111 --installation-id 222 --private-key-path "$KEY" >/dev/null
out="$($CLI auth show)"
if ! grep -q 'auth.*app' <<<"$out"; then
    echo "FAIL: expected mode 'app' after set-mode"; echo "$out"; exit 1
fi
if ! grep -q "111" <<<"$out"; then
    echo "FAIL: expected app_id 111 in show"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk auth show MUST NOT print token values"
# (no real token here, but ensure no env-var-value leakage in output)
SYNAPSE_CLERK_TOKEN="ghp_supersecret" $CLI auth show > "$TMP/show.out"
if grep -q "ghp_supersecret" "$TMP/show.out"; then
    echo "FAIL: token leaked in 'auth show'"; cat "$TMP/show.out"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk auth set-mode pat"
$CLI auth set-mode pat >/dev/null
out="$($CLI auth show)"
if ! grep -q 'auth.*pat' <<<"$out"; then
    echo "FAIL: expected mode 'pat' after set-mode pat"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk auth probe in PAT mode with no env + no gh ambient"
# Shadow `gh` with a stub that exits non-zero, while keeping the real PATH intact.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/gh" <<'STUB'
#!/usr/bin/env bash
exit 1
STUB
chmod +x "$TMP/bin/gh"
set +e
PATH="$TMP/bin:$PATH" $CLI auth probe > "$TMP/probe.out" 2>&1
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
    echo "FAIL: expected non-zero exit, got 0"; cat "$TMP/probe.out"; exit 1
fi
if ! grep -qi "not authenticated\|AuthError\|no PAT" "$TMP/probe.out"; then
    echo "FAIL: expected error message about no auth"; cat "$TMP/probe.out"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk auth probe in PAT mode with token in env"
SYNAPSE_CLERK_TOKEN="ghp_test" $CLI auth probe > "$TMP/probe2.out" 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "FAIL: expected exit 0 with token set"; cat "$TMP/probe2.out"; exit 1
fi
if ! grep -qi "PAT" "$TMP/probe2.out"; then
    echo "FAIL: expected PAT in probe output"; cat "$TMP/probe2.out"; exit 1
fi
# Token value MUST NOT appear
if grep -q "ghp_test" "$TMP/probe2.out"; then
    echo "FAIL: probe output leaked the token value"; cat "$TMP/probe2.out"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk doctor reports auth state (PAT mode, env set)"
SYNAPSE_CLERK_TOKEN="x" $CLI doctor > "$TMP/doc.out" 2>&1 || true
if ! grep -qi "auth" "$TMP/doc.out"; then
    echo "FAIL: expected doctor to mention auth"; cat "$TMP/doc.out"; exit 1
fi
if ! grep -qi "PAT" "$TMP/doc.out"; then
    echo "FAIL: expected PAT mode in doctor output"; cat "$TMP/doc.out"; exit 1
fi
echo "ok"

echo ""
echo "==> clerk doctor in App mode without --probe-auth (no API call)"
$CLI auth set-mode app --app-id 111 --installation-id 222 --private-key-path "$KEY" >/dev/null
$CLI doctor > "$TMP/doc2.out" 2>&1 || true
if ! grep -qi "App" "$TMP/doc2.out"; then
    echo "FAIL: expected 'App' in doctor output (App mode)"; cat "$TMP/doc2.out"; exit 1
fi
echo "ok"

echo ""
echo "All clerk auth CLI smoke tests passed."
