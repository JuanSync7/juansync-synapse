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
            count=$((count + 1))
        done < <(find "$search_dir" -name "SKILL.md" -type f)
    done

    echo ""
    echo "Installed $count skill(s) → $target_dir [$label]"
}
