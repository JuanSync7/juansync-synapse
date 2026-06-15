# commands-skills.sh — skill installation and packaging commands
# Sourced by install.sh; do not execute directly.
# Depends on: common.sh (TARGET, CODEX_GLOBAL_TARGET, _install_skills_to, usage)

cmd_install() {
    # Strip --force flag and apply pre-install git restore on source paths.
    # Drift-resolution UX (T4): `cortex install --force [<artifact>]` discards
    # local edits to the source tree before re-installing.
    local force=0
    local args=()
    for a in "$@"; do
        if [ "$a" = "--force" ]; then
            force=1
        else
            args+=("$a")
        fi
    done

    if [ "$force" = "1" ]; then
        _force_restore_sources "${args[@]}"
    fi

    _install_skills_to "$TARGET" "claude" "${args[@]}"
}

# Discard local edits in source paths before reinstall. If no args (or 'all'),
# restore every artifact path recorded in the lockfile that lives under the
# repo. With explicit args, restore only matching source paths.
# Resolves <artifact> against the lockfile via lockfile_cli.
_force_restore_sources() {
    if [ ! -d "$REPO_ROOT/.git" ] && [ ! -f "$REPO_ROOT/.git" ]; then
        echo "  WARN  --force requested but $REPO_ROOT is not a git repo; skipping restore"
        return 0
    fi

    local targets=("$@")

    export REPO_ROOT
    if [ "${#targets[@]}" -eq 0 ] || [ "${targets[0]}" = "all" ]; then
        # Restore all source paths in lockfile.
        local paths
        paths="$(python3 - <<'PY'
import os, sys, pathlib
sys.path.insert(0, os.environ['REPO_ROOT'] + '/scripts/lib')
import synapse_paths, lockfile as lf_mod
lf = lf_mod.load(synapse_paths.lockfile_path())
for a in lf.artifacts.values():
    print(a.source_path)
PY
)"
        for p in $paths; do
            git -C "$REPO_ROOT" checkout -- "$p" 2>/dev/null || true
            git -C "$REPO_ROOT" clean -fd -- "$p" 2>/dev/null || true
            echo "  force restored $p"
        done
        return 0
    fi

    # Treat each arg as a path or as an artifact key.
    for t in "${targets[@]}"; do
        if [ -d "$REPO_ROOT/$t" ]; then
            git -C "$REPO_ROOT" checkout -- "$t" 2>/dev/null || true
            git -C "$REPO_ROOT" clean -fd -- "$t" 2>/dev/null || true
            echo "  force restored $t"
        else
            # Try to resolve as artifact key via lockfile.
            local resolved
            resolved="$(python3 - "$t" <<'PY' 2>/dev/null
import os, sys, pathlib
sys.path.insert(0, os.environ['REPO_ROOT'] + '/scripts/lib')
import synapse_paths, lockfile as lf_mod, drift_resolve as dr
lf = lf_mod.load(synapse_paths.lockfile_path())
try:
    key = dr.resolve_key(sys.argv[1], lf)
except Exception:
    sys.exit(1)
print(lf.artifacts[key].source_path)
PY
)"
            if [ -n "$resolved" ]; then
                git -C "$REPO_ROOT" checkout -- "$resolved" 2>/dev/null || true
                git -C "$REPO_ROOT" clean -fd -- "$resolved" 2>/dev/null || true
                echo "  force restored $resolved (from $t)"
            else
                echo "  WARN  --force: cannot resolve $t to a source path; skipping"
            fi
        fi
    done
}

cmd_install_codex() {
    _install_skills_to "$CODEX_GLOBAL_TARGET" "codex-global" "$@"
}

cmd_install_codex_project() {
    local project_target="${PWD}/.agents/skills"
    _install_skills_to "$project_target" "codex-project" "$@"
}

cmd_install_gemini() {
    # Ensure the extension manifest exists so Gemini CLI discovers skills
    _ensure_gemini_manifest
    _install_skills_to "$GEMINI_SKILLS_TARGET" "gemini" "$@"
}

_ensure_gemini_manifest() {
    local manifest="$GEMINI_EXT_DIR/gemini-extension.json"
    mkdir -p "$GEMINI_EXT_DIR"

    if [ -f "$manifest" ]; then
        return
    fi

    cat > "$manifest" << 'MANIFEST'
{
  "name": "ai-synapse",
  "version": "1.0.0",
  "description": "ai-synapse skill library — installed via scripts/install.sh"
}
MANIFEST
    echo "  init  gemini-extension.json (created manifest)"
}

cmd_zip() {
    if [ $# -eq 0 ]; then
        echo "Error: specify at least one path (or 'all')"
        usage
        exit 1
    fi

    mkdir -p "$DIST_DIR"

    local count=0

    for path in "$@"; do
        if [ "$path" = "all" ]; then
            path="."
        fi

        local search_dir="$SKILLS_DIR/$path"
        if [ ! -d "$search_dir" ]; then
            echo "Error: '$path' is not a directory in ai-skills"
            exit 1
        fi

        while IFS= read -r skill_md; do
            local skill_dir
            skill_dir="$(dirname "$skill_md")"
            local skill_name
            skill_name="$(basename "$skill_dir")"
            local zip_path="$DIST_DIR/${skill_name}.zip"

            # Build zip from skill directory, excluding non-execution files
            python3 -c "
import zipfile, os, fnmatch, sys
exclude = ['research/*', 'test-inputs/*', 'EVAL.md', 'PROGRAM.md', 'SCOPE.md',
           '.brainstorm-*', '.decision-memo-*', '*.pyc', '__pycache__/*']
skill_dir = sys.argv[1]
zip_path = sys.argv[2]
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d + '/', p) for p in exclude)]
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, skill_dir)
            if not any(fnmatch.fnmatch(rel, p) for p in exclude):
                zf.write(full, rel)
" "$skill_dir" "$zip_path"

            echo "  zip   $skill_name → dist/${skill_name}.zip"
            count=$((count + 1))
        done < <(find "$search_dir" -name "SKILL.md" -type f)
    done

    echo ""
    echo "Packaged $count skill(s) → $DIST_DIR"
}
