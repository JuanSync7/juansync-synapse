# commands-manage.sh — listing, cleanup, agents, identity, and diagnostics
# Sourced by install.sh; do not execute directly.
# Depends on: common.sh (SKILLS_DIR, TARGET, AGENTS_SOURCE, AGENTS_TARGET, CODEX_GLOBAL_TARGET)

cmd_list() {
    if [ ! -d "$TARGET" ]; then
        echo "No skills installed."
        return
    fi

    echo "Installed skills ($TARGET):"
    for link in "$TARGET"/*/; do
        [ -L "${link%/}" ] || continue
        local name
        name="$(basename "$link")"
        local real
        real="$(readlink "${link%/}")"
        # Get relative path from SKILLS_DIR
        local rel="${real#$SKILLS_DIR/}"
        echo "  $name → $rel"
    done
}

cmd_available() {
    echo "Available skills (src/):"
    while IFS= read -r skill_md; do
        local skill_dir
        skill_dir="$(dirname "$skill_md")"
        local skill_name
        skill_name="$(basename "$skill_dir")"
        local rel="${skill_dir#$SKILLS_DIR/}"
        local desc
        desc="$(grep '^description:' "$skill_md" | head -1 | sed 's/^description: //' | cut -c1-60)"
        printf "  %-35s %s\n" "$rel" "$desc"
    done < <(find "$SKILLS_DIR/synapse/skills" "$SKILLS_DIR/src/skills" -name "SKILL.md" -type f 2>/dev/null | sort)

    local external_dir="$SKILLS_DIR/external"
    if [ -d "$external_dir" ]; then
        local ext_count=0
        local ext_output=""
        while IFS= read -r skill_md; do
            local skill_dir
            skill_dir="$(dirname "$skill_md")"
            local skill_name
            skill_name="$(basename "$skill_dir")"
            local rel="${skill_dir#$SKILLS_DIR/}"
            local desc
            desc="$(grep '^description:' "$skill_md" | head -1 | sed 's/^description: //' | cut -c1-60)"
            ext_output+="$(printf "  %-35s %s\n" "$rel" "$desc")"$'\n'
            ext_count=$((ext_count + 1))
        done < <(find "$external_dir" -name "SKILL.md" -type f 2>/dev/null | sort)

        if [ "$ext_count" -gt 0 ]; then
            echo ""
            echo "Available skills (external/):"
            echo -n "$ext_output"
        fi
    fi
}

cmd_clean() {
    if [ ! -d "$TARGET" ]; then
        echo "Nothing to clean."
        return
    fi

    local count=0
    for link in "$TARGET"/*; do
        if [ -L "$link" ]; then
            local real
            real="$(readlink "$link")"
            # Remove symlinks pointing into this repo OR dangling symlinks (stale from a renamed/moved repo)
            if [[ "$real" == "$SKILLS_DIR"* ]] || [ ! -e "$link" ]; then
                local _name
                _name="$(basename "$link")"
                rm "$link"
                echo "  rm  $_name"
                _lockfile_drop_artifact "skill" "$_name"
                count=$((count + 1))
            fi
        fi
    done

    # Also clean agent symlinks in ~/.claude/agents/
    if [ -d "$AGENTS_TARGET" ]; then
        for link in "$AGENTS_TARGET"/*; do
            if [ -L "$link" ]; then
                local real
                real="$(readlink "$link")"
                if [[ "$real" == "$SKILLS_DIR"* ]] || [ ! -e "$link" ]; then
                    local _name
                    _name="$(basename "$link")"
                    rm "$link"
                    echo "  rm  $_name (agent)"
                    _lockfile_drop_artifact "agent" "${_name%.md}"
                    count=$((count + 1))
                fi
            fi
        done
    fi

    # Also clean Codex global symlinks in ~/.codex/skills/
    if [ -d "$CODEX_GLOBAL_TARGET" ]; then
        for link in "$CODEX_GLOBAL_TARGET"/*; do
            if [ -L "$link" ]; then
                local real
                real="$(readlink "$link")"
                if [[ "$real" == "$SKILLS_DIR"* ]] || [ ! -e "$link" ]; then
                    rm "$link"
                    echo "  rm  $(basename "$link") (codex)"
                    count=$((count + 1))
                fi
            fi
        done
    fi

    # Also clean Gemini extension symlinks in ~/.gemini/extensions/ai-synapse/skills/
    if [ -d "$GEMINI_SKILLS_TARGET" ]; then
        for link in "$GEMINI_SKILLS_TARGET"/*; do
            if [ -L "$link" ]; then
                local real
                real="$(readlink "$link")"
                if [[ "$real" == "$SKILLS_DIR"* ]] || [ ! -e "$link" ]; then
                    rm "$link"
                    echo "  rm  $(basename "$link") (gemini)"
                    count=$((count + 1))
                fi
            fi
        done
        # Remove manifest if we created it and no skills remain
        if [ -f "$GEMINI_EXT_DIR/gemini-extension.json" ] && [ -z "$(ls -A "$GEMINI_SKILLS_TARGET" 2>/dev/null)" ]; then
            rm "$GEMINI_EXT_DIR/gemini-extension.json"
            rmdir "$GEMINI_SKILLS_TARGET" 2>/dev/null || true
            rmdir "$GEMINI_EXT_DIR" 2>/dev/null || true
            echo "  rm  gemini-extension.json (manifest)"
            count=$((count + 1))
        fi
    fi

    # Also clean identity symlinks in ~/.claude/
    local CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
    for identity_file in "SOUL.md" "stakeholder.md"; do
        local link="$CLAUDE_DIR/$identity_file"
        if [ -L "$link" ]; then
            local real
            real="$(readlink "$link")"
            if [[ "$real" == "$SKILLS_DIR"* ]] || [ ! -e "$link" ]; then
                rm "$link"
                echo "  rm  $identity_file (identity)"
                count=$((count + 1))
            fi
        fi
    done

    _lockfile_stamp

    echo ""
    echo "Removed $count symlink(s)"
}

cmd_install_identity() {
    local IDENTITY_DIR="$SKILLS_DIR/identity"
    local CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

    if [ ! -d "$IDENTITY_DIR" ]; then
        echo "Error: identity/ directory not found"
        exit 1
    fi

    local count=0

    # Files to install: source_name -> target_name
    # SOUL.template.md is excluded (repo-only, not installed)
    local src_files=("SOUL.md" "STAKEHOLDER.md")
    local tgt_files=("SOUL.md" "stakeholder.md")

    for i in "${!src_files[@]}"; do
        local src="$IDENTITY_DIR/${src_files[$i]}"
        local target_name="${tgt_files[$i]}"
        local target="$CLAUDE_DIR/$target_name"

        if [ ! -f "$src" ]; then
            echo "  skip  ${src_files[$i]} (not found)"
            continue
        fi

        if [ -L "$target" ]; then
            local existing
            existing="$(readlink "$target")"
            if [ "$existing" = "$src" ]; then
                echo "  skip  $target_name (already installed)"
                continue
            elif [ ! -e "$target" ]; then
                rm "$target"
                echo "  fix   $target_name (was broken: $existing)"
            else
                echo "  WARN  $target_name collision: already points to $existing"
                continue
            fi
        fi

        if [ -f "$target" ]; then
            echo "  WARN  $target_name exists as regular file — back up and remove before installing"
            continue
        fi

        ln -s "$src" "$target"
        echo "  add   $target_name -> identity/${src_files[$i]}"
        count=$((count + 1))
    done

    echo ""
    echo "Installed $count identity file(s) -> $CLAUDE_DIR"
}

cmd_install_agents() {
    if [ ! -d "$AGENTS_SOURCE" ] && [ ! -d "$AGENTS_SOURCE_ALT" ]; then
        echo "Error: neither synapse/agents/ nor src/agents/ directory found"
        exit 1
    fi

    mkdir -p "$AGENTS_TARGET"

    local count=0

    # Recurse into domain subdirs across both framework and adopter agent roots.
    while IFS= read -r src; do
        [ -f "$src" ] || continue
        local name
        name="$(basename "$src")"
        local target="$AGENTS_TARGET/$name"

        if [ -L "$target" ]; then
            local existing
            existing="$(readlink "$target")"
            if [ "$existing" = "$src" ]; then
                echo "  skip  $name (already installed)"
                continue
            elif [ ! -e "$target" ]; then
                rm "$target"
                echo "  fix   $name (was broken: $existing)"
            else
                echo "  WARN  $name collision: already points to $existing"
                continue
            fi
        fi

        ln -s "$src" "$target"
        echo "  add   $name"
        # Strip ".md" off agent filenames for the lockfile key.
        local agent_key="${name%.md}"
        _lockfile_record_artifact "agent" "$agent_key" "$src" "$target"
        count=$((count + 1))
    done < <(find "$AGENTS_SOURCE" "$AGENTS_SOURCE_ALT" -name '*.md' -not -name 'README.md' -type f 2>/dev/null | sort)

    _lockfile_stamp

    echo ""
    echo "Installed $count agent(s) → $AGENTS_TARGET"
}

cmd_doctor_symlinks() {
    local broken=0

    echo "Checking external/ submodules..."
    check_external_submodules >/dev/null
    if [ "${#_EMPTY_SUBMODULES[@]}" -gt 0 ]; then
        for sub in "${_EMPTY_SUBMODULES[@]}"; do
            echo "  EMPTY   external/$sub (submodule not initialized)"
        done
        echo "  Run 'git submodule update --init' or 'make init' to fix."
    else
        echo "  All external submodules initialized."
    fi
    echo ""

    echo "Checking skills ($TARGET)..."
    if [ -d "$TARGET" ]; then
        for link in "$TARGET"/*; do
            [ -L "$link" ] || continue
            if [ ! -e "$link" ]; then
                echo "  BROKEN  $(basename "$link") -> $(readlink "$link")"
                broken=$((broken + 1))
            fi
        done
    fi

    echo "Checking agents ($AGENTS_TARGET)..."
    if [ -d "$AGENTS_TARGET" ]; then
        for link in "$AGENTS_TARGET"/*; do
            [ -L "$link" ] || continue
            if [ ! -e "$link" ]; then
                echo "  BROKEN  $(basename "$link") -> $(readlink "$link")"
                broken=$((broken + 1))
            fi
        done
    fi

    echo "Checking codex skills ($CODEX_GLOBAL_TARGET)..."
    if [ -d "$CODEX_GLOBAL_TARGET" ]; then
        for link in "$CODEX_GLOBAL_TARGET"/*; do
            [ -L "$link" ] || continue
            if [ ! -e "$link" ]; then
                echo "  BROKEN  $(basename "$link") -> $(readlink "$link")"
                broken=$((broken + 1))
            fi
        done
    fi

    echo "Checking gemini skills ($GEMINI_SKILLS_TARGET)..."
    if [ -d "$GEMINI_SKILLS_TARGET" ]; then
        for link in "$GEMINI_SKILLS_TARGET"/*; do
            [ -L "$link" ] || continue
            if [ ! -e "$link" ]; then
                echo "  BROKEN  $(basename "$link") -> $(readlink "$link")"
                broken=$((broken + 1))
            fi
        done
    fi

    echo ""
    if [ "$broken" -eq 0 ]; then
        echo "All symlinks healthy."
    else
        echo "$broken broken symlink(s) found. Run 'install all' to auto-fix, or 'clean' to remove all."
    fi
}
