#!/usr/bin/env bash
# Smoke-test scripts/lib/telemetry_cli.py end-to-end.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/telemetry_cli.py"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export HOME="$TMP"
unset SYNAPSE_TELEMETRY_DISABLE || true

EVENTS_FILE="$TMP/.synapse/events.jsonl"

# 1. status with no config -> defaults
OUT="$($CLI status)"
echo "$OUT" | grep -q "enabled" || { echo "FAIL: status missing 'enabled'"; echo "$OUT"; exit 1; }
echo "$OUT" | grep -q "file" || { echo "FAIL: status missing 'file'"; echo "$OUT"; exit 1; }
echo "  ok   status defaults"

# 2. status --json parses
JSON="$($CLI status --json)"
python3 -c "
import json,sys
d = json.loads('''$JSON''')
assert d['enabled'] is True, d
assert 'file' in d['sinks'], d
assert d['config_path'].endswith('config.toml'), d
" || { echo "FAIL: status --json invalid"; echo "$JSON"; exit 1; }
echo "  ok   status --json"

# 3. emit writes a line
$CLI emit drift_detected --artifact skill/foo --metadata k=v >/dev/null
[[ -f "$EVENTS_FILE" ]] || { echo "FAIL: events file not created"; exit 1; }
LINE="$(tail -n 1 "$EVENTS_FILE")"
python3 -c "
import json
d = json.loads('''$LINE''')
assert d['event_type'] == 'drift_detected', d
assert d['artifact'] == 'skill/foo', d
assert d['metadata']['k'] == 'v', d
" || { echo "FAIL: emit line invalid"; echo "$LINE"; exit 1; }
echo "  ok   emit"

# 4. emit with SYNAPSE_TELEMETRY_DISABLE -> no-op
SIZE_BEFORE="$(wc -c < "$EVENTS_FILE")"
SYNAPSE_TELEMETRY_DISABLE=1 $CLI emit install --artifact skill/bar >/dev/null
SIZE_AFTER="$(wc -c < "$EVENTS_FILE")"
[[ "$SIZE_BEFORE" == "$SIZE_AFTER" ]] || { echo "FAIL: emit not suppressed by env"; exit 1; }
echo "  ok   emit suppressed by SYNAPSE_TELEMETRY_DISABLE"

# 5. rotate creates .gz and resets file
$CLI emit install --artifact a >/dev/null
$CLI emit install --artifact b >/dev/null
$CLI rotate >/dev/null
GZS=( "$TMP/.synapse"/events.jsonl.*.gz )
[[ -f "${GZS[0]}" ]] || { echo "FAIL: no .gz produced"; ls -la "$TMP/.synapse"; exit 1; }
[[ ! -s "$EVENTS_FILE" ]] || { echo "FAIL: events.jsonl not truncated"; exit 1; }
# verify gz contents readable
python3 -c "
import gzip
with gzip.open('${GZS[0]}','rb') as f:
    data = f.read().decode()
assert 'install' in data, data
" || { echo "FAIL: gz contents bad"; exit 1; }
echo "  ok   rotate creates .gz and truncates"

# 6. rotate when file sink not configured -> error
TMP2="$(mktemp -d)"
HOME2="$TMP2"
mkdir -p "$HOME2/.synapse"
cat > "$HOME2/.synapse/config.toml" <<'EOF'
[telemetry]
enabled = true
sinks = ["none"]
EOF
if HOME="$HOME2" $CLI rotate 2>/dev/null; then
    echo "FAIL: rotate did not refuse without file sink"
    rm -rf "$TMP2"
    exit 1
fi
rm -rf "$TMP2"
echo "  ok   rotate refuses without file sink"

echo ""
echo "All telemetry_cli smoke checks passed."
