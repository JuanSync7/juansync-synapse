#!/usr/bin/env bash
# Smoke-test scripts/lib/lockfile_cli.py end-to-end.
# Each subcommand against an ephemeral SYNAPSE_PROJECT, then parse with tomllib.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="python3 $REPO_ROOT/scripts/lib/lockfile_cli.py"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

export SYNAPSE_PROJECT="$TMP"
mkdir -p "$TMP/.synapse"

# Create a fake artifact directory under the repo root so hashing can resolve it.
# (CLI uses git rev-parse --show-toplevel to find repo root.)
FAKE_SRC="synapse/skills/_test_lockfile_cli_tmp"
mkdir -p "$REPO_ROOT/$FAKE_SRC"
echo "x" > "$REPO_ROOT/$FAKE_SRC/SKILL.md"
trap 'rm -rf "$REPO_ROOT/$FAKE_SRC" "$TMP"' EXIT

# 1. path subcommand
LOCK_PATH="$($CLI path)"
[[ "$LOCK_PATH" == "$TMP/.synapse/installed.lock" ]] || {
    echo "FAIL: path returned $LOCK_PATH"; exit 1; }
echo "  ok   path"

# 2. upsert-artifact
$CLI upsert-artifact \
    --key "skill/_test_lockfile_cli_tmp" \
    --type skill \
    --source-path "$FAKE_SRC" \
    --install-path "$HOME/.claude/skills/_test_lockfile_cli_tmp" >/dev/null
[[ -f "$LOCK_PATH" ]] || { echo "FAIL: lockfile not created"; exit 1; }

python3 -c "
import tomllib, sys
d = tomllib.loads(open('$LOCK_PATH').read())
assert d['schema_version'] == 1, d
assert 'skill/_test_lockfile_cli_tmp' in d['artifact'], d
a = d['artifact']['skill/_test_lockfile_cli_tmp']
assert a['type'] == 'skill', a
assert a['status'] == 'installed', a
assert a['content_hash'].startswith('sha256:'), a
"
echo "  ok   upsert-artifact"

# 3. stamp
$CLI stamp >/dev/null
python3 -c "
import tomllib
d = tomllib.loads(open('$LOCK_PATH').read())
assert d['synapse_sha'], d
assert d['installed_at'].endswith('Z'), d
assert d['machine_id'], d
assert d['synapse_repo'], d
"
echo "  ok   stamp"

# 4. remove
$CLI remove --key "skill/_test_lockfile_cli_tmp" >/dev/null
python3 -c "
import tomllib
d = tomllib.loads(open('$LOCK_PATH').read())
assert 'artifact' not in d or 'skill/_test_lockfile_cli_tmp' not in d.get('artifact', {}), d
"
echo "  ok   remove"

# 5. upsert-external (use the repo itself as a fake submodule — it has a .git)
$CLI upsert-external \
    --key "_self" \
    --submodule-path "." >/dev/null
python3 -c "
import tomllib
d = tomllib.loads(open('$LOCK_PATH').read())
assert '_self' in d['external'], d
e = d['external']['_self']
assert len(e['submodule_sha']) == 40, e
assert e['content_hash'].startswith('sha256:'), e
"
echo "  ok   upsert-external"

# Cleanup external entry so we don't leave noise behind
$CLI remove-external --key "_self" >/dev/null 2>&1 || true

echo "lockfile_cli: all subcommands ok"
