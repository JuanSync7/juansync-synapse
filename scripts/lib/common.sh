# common.sh — shared variables and utilities for install.sh
# Sourced by install.sh; do not execute directly.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="$REPO_ROOT"

# Claude Code targets
TARGET="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
# Framework agents live in synapse/agents; adopter agents in src/agents.
# Default to synapse/ for the framework repo; cmd_install_agents iterates both.
AGENTS_SOURCE="$SKILLS_DIR/synapse/agents"
AGENTS_SOURCE_ALT="$SKILLS_DIR/src/agents"
AGENTS_TARGET="${CLAUDE_AGENTS_DIR:-$HOME/.claude/agents}"

# Codex CLI targets
CODEX_GLOBAL_TARGET="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"

# Gemini CLI targets
GEMINI_EXT_DIR="${GEMINI_EXT_DIR:-$HOME/.gemini/extensions/ai-synapse}"
GEMINI_SKILLS_TARGET="$GEMINI_EXT_DIR/skills"

DIST_DIR="$SKILLS_DIR/dist"

# Path to the lockfile CLI. Invoked after symlink ops to record state in
# installed.lock. Honors SYNAPSE_LOCKFILE_DISABLE for tests/rollback.
LOCKFILE_CLI="$REPO_ROOT/scripts/lib/lockfile_cli.py"

# Run a lockfile_cli subcommand if not disabled. Failures are non-fatal so a
# bad lockfile call cannot break installs.
_lockfile() {
    [ -n "${SYNAPSE_LOCKFILE_DISABLE:-}" ] && return 0
    [ -f "$LOCKFILE_CLI" ] || return 0
    python3 "$LOCKFILE_CLI" "$@" >/dev/null 2>&1 || true
}

# Record an artifact symlink in installed.lock.
# Args: <type> <name> <abs-source-dir> <abs-target-symlink>
_lockfile_record_artifact() {
    local type="$1" name="$2" src="$3" install="$4"
    # source_path must be repo-relative for hashing to work cross-machine.
    local rel="${src#$REPO_ROOT/}"
    _lockfile upsert-artifact \
        --key "$type/$name" \
        --type "$type" \
        --source-path "$rel" \
        --install-path "$install"
}

# Record an external/ submodule. Args: <name>
_lockfile_record_external() {
    local name="$1"
    _lockfile upsert-external \
        --key "$name" \
        --submodule-path "external/$name"
}

# Drop an artifact entry. Args: <type> <name>
_lockfile_drop_artifact() {
    local type="$1" name="$2"
    _lockfile remove --key "$type/$name"
}

_lockfile_stamp() {
    _lockfile stamp
}

usage() {
    echo "Usage: ai-skills <command> [args...]"
    echo ""
    echo "Global commands:"
    echo "  list                List currently installed skills"
    echo "  available           List all available skills in the repo"
    echo "  doctor              Check for broken symlinks"
    echo ""
    echo "Claude Code:"
    echo "  install <path...>   Install skills to ~/.claude/skills/"
    echo "  agents              Install agent definitions to ~/.claude/agents/"
    echo "  identity            Install identity files (SOUL.md, stakeholder.md)"
    echo "  zip <path...>       Package skills as .zip for Claude Desktop"
    echo "  clean               Remove all installed symlinks (all harnesses)"
    echo ""
    echo "Codex CLI:"
    echo "  codex <path...>     Install skills to ~/.codex/skills/ (global)"
    echo "  codex-project <path...>  Install skills to .agents/skills/ (project)"
    echo ""
    echo "Gemini CLI:"
    echo "  gemini <path...>    Install skills to ~/.gemini/extensions/ai-synapse/"
    echo ""
    echo "Examples:"
    echo "  ai-skills install all           # Claude Code: install everything"
    echo "  ai-skills codex all             # Codex CLI: install everything (global)"
    echo "  ai-skills codex-project all     # Codex CLI: install to current project"
    echo "  ai-skills gemini all            # Gemini CLI: install everything"
    echo "  ai-skills install synapse/skills/skill src/skills/docs"
    echo "  ai-skills zip all"
}

# Inspect external/ submodules for empty (uninitialized) directories.
# Sets _EMPTY_SUBMODULES array; returns count via stdout.
check_external_submodules() {
    local external_dir="$REPO_ROOT/external"
    _EMPTY_SUBMODULES=()

    [ -d "$external_dir" ] || return 0

    for sub in "$external_dir"/*/; do
        [ -d "$sub" ] || continue
        # Empty if no entries other than . and ..
        if [ -z "$(ls -A "$sub" 2>/dev/null)" ]; then
            _EMPTY_SUBMODULES+=("$(basename "$sub")")
        fi
    done

    echo "${#_EMPTY_SUBMODULES[@]}"
}

# Install alias symlinks declared in a skill's `aliases:` frontmatter.
# Aliases are convenience handles (taxonomy/SKILL_TAXONOMY.md "Aliases"). Each alias is
# MATERIALIZED as a real directory — companions symlinked, but SKILL.md regenerated with
# `name:` rewritten to the alias and an `alias-of: <canonical>` marker. A raw dir symlink
# would leave the frontmatter name disagreeing with the directory name, so the harness
# (whichever key it uses) would see a duplicate or inconsistent entry. The marker makes
# alias dirs detectable by the collision guard and `cortex clean`. An alias path holding
# anything that is not OUR alias of THIS skill is never overwritten — fail loud, skip.
_install_skill_aliases() {
    local skill_md="$1" skill_dir="$2" skill_name="$3" target_dir="$4"

    local alias_line
    alias_line="$(sed -n '/^---$/,/^---$/p' "$skill_md" | grep '^aliases:' | sed 's/^aliases: *//' | tr -d "[]\"'" || true)"
    [ -z "$alias_line" ] && return 0

    local alias
    IFS=',' read -ra _aliases <<< "$alias_line"
    for alias in "${_aliases[@]}"; do
        alias="$(echo "$alias" | xargs)"
        [ -z "$alias" ] && continue
        local alias_path="$target_dir/$alias"

        if [ -L "$alias_path" ]; then
            # Legacy symlink alias from a previous version: ours → upgrade, foreign → refuse
            local existing
            existing="$(readlink "$alias_path")"
            if [ "$existing" = "$skill_dir" ] || [ ! -e "$alias_path" ]; then
                rm "$alias_path"
            else
                echo "  WARN  alias '$alias' collision: symlink to $existing — NOT overwriting (alias squatting refused)"
                continue
            fi
        elif [ -d "$alias_path" ]; then
            if grep -q "^alias-of: $skill_name$" "$alias_path/SKILL.md" 2>/dev/null; then
                rm -rf "$alias_path"   # ours — rebuild fresh below
            else
                echo "  WARN  alias '$alias' collision: a directory '$alias' exists in $target_dir — NOT overwriting"
                continue
            fi
        elif [ -e "$alias_path" ]; then
            echo "  WARN  alias '$alias' collision: '$alias' exists in $target_dir — NOT overwriting"
            continue
        fi

        mkdir -p "$alias_path"
        # Symlink every companion entry; regenerate SKILL.md with the alias identity
        local entry
        for entry in "$skill_dir"/*; do
            [ "$(basename "$entry")" = "SKILL.md" ] && continue
            ln -s "$entry" "$alias_path/$(basename "$entry")"
        done
        sed "s/^name: .*/name: $alias/" "$skill_md" \
            | sed "0,/^name: /s//alias-of: $skill_name\nname: /" > "$alias_path/SKILL.md"
        echo "  alias $alias -> $skill_name (materialized)"
        _lockfile_record_artifact "skill-alias" "$alias" "$skill_dir" "$alias_path"
    done
}

# Generic skill installer — shared by Claude and Codex adapters
_install_skills_to() {
    local target_dir="$1"
    local label="$2"
    shift 2

    if [ $# -eq 0 ]; then
        echo "Error: specify at least one path (or 'all')"
        usage
        exit 1
    fi

    mkdir -p "$target_dir"

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

            # Check for collision
            if [ -L "$target_dir/$skill_name" ]; then
                local existing
                existing="$(readlink "$target_dir/$skill_name")"
                if [ "$existing" = "$skill_dir" ]; then
                    echo "  skip  $skill_name (already installed)"
                    # Still reconcile aliases — they may have been added since first install
                    _install_skill_aliases "$skill_md" "$skill_dir" "$skill_name" "$target_dir"
                    continue
                elif [ ! -e "$target_dir/$skill_name" ]; then
                    rm "$target_dir/$skill_name"
                    echo "  fix   $skill_name (was broken: $existing)"
                else
                    echo "  WARN  $skill_name collision: already points to $existing"
                    continue
                fi
            fi

            ln -s "$skill_dir" "$target_dir/$skill_name"
            echo "  add   $skill_name"
            _lockfile_record_artifact "skill" "$skill_name" "$skill_dir" "$target_dir/$skill_name"
            count=$((count + 1))

            _install_skill_aliases "$skill_md" "$skill_dir" "$skill_name" "$target_dir"
        done < <(find "$search_dir" -name "SKILL.md" -type f)
    done

    _lockfile_stamp

    echo ""
    echo "Installed $count skill(s) → $target_dir [$label]"
}
