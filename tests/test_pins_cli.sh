#!/usr/bin/env bash
# Smoke-test scripts/lib/pins_cli.py end-to-end.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/pins_cli.py"

TMP="$(mktemp -d)"
FAKE_REPO="$TMP/fakerepo"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Build a tiny fake git repo to act as the synapse source.
mkdir -p "$FAKE_REPO"
git -C "$FAKE_REPO" init -q -b main
git -C "$FAKE_REPO" config user.email t@t
git -C "$FAKE_REPO" config user.name t
echo "1" > "$FAKE_REPO/x"
git -C "$FAKE_REPO" add .
git -C "$FAKE_REPO" commit -q -m "c1"
git -C "$FAKE_REPO" tag v1.0.0
echo "2" > "$FAKE_REPO/x"
git -C "$FAKE_REPO" add .
git -C "$FAKE_REPO" commit -q -m "c2"
git -C "$FAKE_REPO" tag v1.2.3

# Project-scope the pins.toml via SYNAPSE_PROJECT.
export SYNAPSE_PROJECT="$TMP"
mkdir -p "$TMP/.synapse"
# Tell pins_cli where to resolve pins against.
export SYNAPSE_REPO_ROOT="$FAKE_REPO"

# 1. path
PINS_PATH="$($CLI path)"
[[ "$PINS_PATH" == "$TMP/.synapse/pins.toml" ]] || {
    echo "FAIL: path returned $PINS_PATH"; exit 1; }
echo "  ok   path"

# 2. current with no file → "latest"
CUR="$($CLI current)"
[[ "$CUR" == "latest" ]] || { echo "FAIL: current default = $CUR"; exit 1; }
echo "  ok   current (default latest)"

# 3. pin v1.0.0
$CLI pin v1.0.0 >/dev/null
[[ -f "$PINS_PATH" ]] || { echo "FAIL: pins.toml not created"; exit 1; }
python3 -c "
import tomllib
d = tomllib.loads(open('$PINS_PATH').read())
assert d['synapse']['pin'] == 'v1.0.0', d
"
echo "  ok   pin v1.0.0"

# 4. pin invalid-junk should fail nonzero
if $CLI pin invalid-junk 2>/dev/null; then
    echo "FAIL: invalid pin should have errored"; exit 1
fi
echo "  ok   pin rejects invalid value"

# 5. unpin → latest
$CLI unpin >/dev/null
python3 -c "
import tomllib
d = tomllib.loads(open('$PINS_PATH').read())
assert d['synapse']['pin'] == 'latest', d
"
echo "  ok   unpin"

# 6. bump from latest → highest stable tag
$CLI bump >/dev/null
python3 -c "
import tomllib
d = tomllib.loads(open('$PINS_PATH').read())
assert d['synapse']['pin'] == 'v1.2.3', d
"
echo "  ok   bump (latest → v1.2.3)"

# 7. bump idempotent on already-tag
OUT="$($CLI bump 2>&1)"
echo "$OUT" | grep -qi "already" || { echo "FAIL: bump should report already frozen, got: $OUT"; exit 1; }
echo "  ok   bump idempotent on tag"

# 8. status human-readable
OUT="$($CLI status)"
echo "$OUT" | grep -q "Pin:" || { echo "FAIL: status missing Pin: line"; exit 1; }
echo "$OUT" | grep -q "Resolved SHA:" || { echo "FAIL: status missing Resolved SHA:"; exit 1; }
echo "$OUT" | grep -q "Pin kind:" || { echo "FAIL: status missing Pin kind:"; exit 1; }
echo "$OUT" | grep -q "Drift summary:" || { echo "FAIL: status missing Drift summary:"; exit 1; }
echo "  ok   status (human)"

# 9. status --json
OUT="$($CLI status --json)"
python3 -c "
import json
d = json.loads('''$OUT''')
assert d['pin'] == 'v1.2.3', d
assert d['kind'] == 'tag', d
assert len(d['resolved_sha']) == 40, d
"
echo "  ok   status --json"

# 10. current
CUR="$($CLI current)"
[[ "$CUR" == "v1.2.3" ]] || { echo "FAIL: current = $CUR"; exit 1; }
echo "  ok   current"

echo "pins_cli: all subcommands ok"
