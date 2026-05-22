#!/usr/bin/env bash
# @name: sync
# @description: Sync registries and READMEs from disk state — detect and fix drift
# @audience: maintainer
# @action: repair
# @scope: repo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- Colors ---
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Globals for summary ---
STALE_TOTAL=0
PATH_MISMATCH_TOTAL=0
README_ISSUES_TOTAL=0

# --- Helper functions ---

# Extract frontmatter field from a markdown file
extract_field() {
    local file="$1" field="$2"
    sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null \
        | sed '1d;$d' \
        | grep "^${field}:" \
        | head -1 \
        | sed "s/^${field}: *//" \
        | tr -d '"' \
        | tr -d "'" \
        || true
}

# Extract all entries from a registry file as name|path pairs
# Writes to a temp file to avoid subshell issues
extract_registry_entries() {
    local file="$1" outfile="$2"
    > "$outfile"
    [[ -f "$file" ]] || return 0
    while IFS= read -r line; do
        # Skip separator rows
        if [[ "$line" =~ ^\|[[:space:]]*-+ ]]; then continue; fi
        # Skip if line doesn't contain a markdown link
        if [[ ! "$line" =~ \[.*\]\(.*\) ]]; then continue; fi
        # Extract [name](path) from table row
        local name path
        name=$(echo "$line" | sed -n 's/.*\[\([^]]*\)\](\([^)]*\)).*/\1/p' | head -1)
        path=$(echo "$line" | sed -n 's/.*\[\([^]]*\)\](\([^)]*\)).*/\2/p' | head -1)
        if [[ -n "$name" && -n "$path" ]]; then
            echo "${name}|${path}" >> "$outfile"
        fi
    done < <(grep '^\s*|' "$file" 2>/dev/null || true)
}

# Resolve a registry path to an absolute path
# Handles both ../src/... (relative to registry/) and src/... (relative to repo root)
resolve_registry_path() {
    local raw_path="$1" registry_file="$2"
    local registry_dir
    registry_dir="$(dirname "$registry_file")"

    if [[ "$raw_path" == ../* ]]; then
        realpath -m "${registry_dir}/${raw_path}" 2>/dev/null
    elif [[ "$raw_path" == /* ]]; then
        echo "$raw_path"
    else
        realpath -m "${REPO_ROOT}/${raw_path}" 2>/dev/null
    fi
}

# Extract artifact names from a domain README table, writes to outfile
extract_readme_entries() {
    local file="$1" outfile="$2"
    > "$outfile"
    [[ -f "$file" ]] || return 0
    while IFS= read -r line; do
        # Skip separator rows
        if [[ "$line" =~ ^\|[[:space:]]*-+ ]]; then continue; fi
        # Skip if line doesn't contain a markdown link
        if [[ ! "$line" =~ \[.*\]\(.*\) ]]; then continue; fi
        local name
        name=$(echo "$line" | sed -n 's/.*\[\([^]]*\)\](\([^)]*\)).*/\1/p' | head -1)
        if [[ -n "$name" ]]; then
            echo "$name" >> "$outfile"
        fi
    done < <(grep '^\s*|' "$file" 2>/dev/null || true)
}

# --- Scan functions ---
# Each writes name|absolute_path lines to a temp file

scan_skills() {
    local outfile="$1"
    > "$outfile"
    # Scan synapse/skills (framework) and src/skills (adopter)
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/synapse/skills" "$REPO_ROOT/src/skills" -name "SKILL.md" -type f 2>/dev/null || true)
    # Scan external/*/skills
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/external" -path "*/skills/*/SKILL.md" -type f 2>/dev/null || true)
}

scan_agents() {
    local outfile="$1"
    > "$outfile"
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/synapse/agents" "$REPO_ROOT/src/agents" -name "*.md" -not -name "README.md" -not -path "*/change_requests/*" -type f 2>/dev/null || true)
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/external" -path "*/agents/*.md" -not -name "README.md" -not -path "*/change_requests/*" -type f 2>/dev/null || true)
}

scan_protocols() {
    local outfile="$1"
    > "$outfile"
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/synapse/protocols" "$REPO_ROOT/src/protocols" -name "*.md" -not -name "README.md" -not -path "*/change_requests/*" -type f 2>/dev/null || true)
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/external" -path "*/protocols/*.md" -not -name "README.md" -not -path "*/change_requests/*" -type f 2>/dev/null || true)
}

scan_tools() {
    local outfile="$1"
    > "$outfile"
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/synapse/tools" "$REPO_ROOT/src/tools" -name "TOOL.md" -type f 2>/dev/null || true)
    while IFS= read -r f; do
        local name
        name=$(extract_field "$f" "name")
        [[ -n "$name" ]] && echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/external" -path "*/tools/*/TOOL.md" -type f 2>/dev/null || true)
}

# --- Load disk map into associative array from scan output file ---
# Usage: load_disk_map <scan_file>
# Populates global DISK_MAP
declare -A DISK_MAP=()

load_disk_map() {
    local scan_file="$1"
    DISK_MAP=()
    while IFS='|' read -r name path; do
        [[ -n "$name" ]] && DISK_MAP["$name"]="$path"
    done < "$scan_file"
}

# --- Status reporting ---

check_type() {
    local type_label="$1"
    local registry_file="$2"
    local scan_fn="$3"
    local artifact_marker="$4"

    local stale=0 path_mismatch=0 missing_readme=0 stale_readme=0

    echo -e "\n${BOLD}${CYAN}[$type_label]${NC}"

    if [[ ! -f "$registry_file" ]]; then
        echo -e "  ${YELLOW}SKIP${NC}: registry file not found: $registry_file"
        return 0
    fi

    # Scan disk
    local scan_tmp
    scan_tmp=$(mktemp)
    $scan_fn "$scan_tmp"
    load_disk_map "$scan_tmp"

    # Extract registry entries
    local reg_tmp
    reg_tmp=$(mktemp)
    extract_registry_entries "$registry_file" "$reg_tmp"

    # Check registry entries against disk
    while IFS='|' read -r reg_name reg_path; do
        [[ -z "$reg_name" ]] && continue
        local abs_path
        abs_path=$(resolve_registry_path "$reg_path" "$registry_file")

        if [[ -z "${DISK_MAP[$reg_name]+x}" ]]; then
            if [[ ! -f "$abs_path" ]]; then
                echo -e "  ${RED}STALE${NC}: '$reg_name' in registry but not found on disk (path: $reg_path)"
                ((stale++)) || true
            else
                echo -e "  ${YELLOW}NAME DRIFT${NC}: '$reg_name' in registry, file exists at $reg_path but name field differs"
                ((path_mismatch++)) || true
            fi
        else
            local disk_path="${DISK_MAP[$reg_name]}"
            if [[ "$abs_path" != "$disk_path" ]]; then
                local rel_actual
                rel_actual=$(realpath --relative-to="$(dirname "$registry_file")" "$disk_path" 2>/dev/null || echo "$disk_path")
                echo -e "  ${YELLOW}PATH MISMATCH${NC}: '$reg_name' -> registry: $reg_path, disk: $rel_actual"
                ((path_mismatch++)) || true
            fi
        fi
    done < "$reg_tmp"

    # Check domain READMEs (only for src/ artifacts)
    local src_dir="$REPO_ROOT/src/${type_label,,}"
    if [[ -d "$src_dir" ]]; then
        local readme_tmp
        readme_tmp=$(mktemp)
        for domain_dir in "$src_dir"/*/; do
            [[ -d "$domain_dir" ]] || continue
            local readme="${domain_dir}README.md"
            [[ -f "$readme" ]] || continue

            extract_readme_entries "$readme" "$readme_tmp"
            local rel_readme
            rel_readme=$(realpath --relative-to="$REPO_ROOT" "$readme")

            # Check for stale README rows
            while IFS= read -r rname; do
                [[ -z "$rname" ]] && continue
                if [[ -z "${DISK_MAP[$rname]+x}" ]]; then
                    echo -e "  ${RED}STALE README ROW${NC}: '$rname' in ${rel_readme} but not on disk"
                    ((stale_readme++)) || true
                fi
            done < "$readme_tmp"

            # Check for missing README rows
            for dname in "${!DISK_MAP[@]}"; do
                local dpath="${DISK_MAP[$dname]}"
                local ddir
                ddir="$(dirname "$dpath")"
                if [[ "$artifact_marker" == "SKILL.md" || "$artifact_marker" == "TOOL.md" ]]; then
                    ddir="$(dirname "$ddir")"
                fi
                local norm_domain norm_ddir
                norm_domain=$(realpath -m "$domain_dir")
                norm_ddir=$(realpath -m "$ddir")
                if [[ "$norm_ddir" == "$norm_domain" ]]; then
                    if ! grep -qx "$dname" "$readme_tmp" 2>/dev/null; then
                        echo -e "  ${YELLOW}MISSING README ROW${NC}: '$dname' exists on disk but not in ${rel_readme}"
                        ((missing_readme++)) || true
                    fi
                fi
            done
        done
        rm -f "$readme_tmp"
    fi

    local total=$((stale + path_mismatch + missing_readme + stale_readme))
    if [[ $total -eq 0 ]]; then
        echo -e "  ${GREEN}OK${NC}: no drift detected"
    fi

    STALE_TOTAL=$((STALE_TOTAL + stale))
    PATH_MISMATCH_TOTAL=$((PATH_MISMATCH_TOTAL + path_mismatch))
    README_ISSUES_TOTAL=$((README_ISSUES_TOTAL + missing_readme + stale_readme))

    rm -f "$scan_tmp" "$reg_tmp"
}

# --- Fix functions ---

fix_type() {
    local type_label="$1"
    local registry_file="$2"
    local scan_fn="$3"
    local artifact_marker="$4"

    echo -e "\n${BOLD}${CYAN}[$type_label]${NC}"

    if [[ ! -f "$registry_file" ]]; then
        echo -e "  ${YELLOW}SKIP${NC}: registry file not found: $registry_file"
        return 0
    fi

    local scan_tmp
    scan_tmp=$(mktemp)
    $scan_fn "$scan_tmp"
    load_disk_map "$scan_tmp"

    local reg_tmp
    reg_tmp=$(mktemp)
    extract_registry_entries "$registry_file" "$reg_tmp"

    # Fix registry entries
    while IFS='|' read -r reg_name reg_path; do
        [[ -z "$reg_name" ]] && continue
        local abs_path
        abs_path=$(resolve_registry_path "$reg_path" "$registry_file")

        if [[ -z "${DISK_MAP[$reg_name]+x}" ]] && [[ ! -f "$abs_path" ]]; then
            local escaped_name
            escaped_name=$(printf '%s' "$reg_name" | sed 's/[]\/$*.^[]/\\&/g')
            sed -i "/| *\[${escaped_name}\]/d" "$registry_file"
            echo -e "  ${GREEN}FIX${NC}: removed stale entry '${reg_name}' from $(basename "$registry_file")"
        elif [[ -n "${DISK_MAP[$reg_name]+x}" ]]; then
            local disk_path="${DISK_MAP[$reg_name]}"
            if [[ "$abs_path" != "$disk_path" ]]; then
                local new_rel_path
                new_rel_path=$(realpath --relative-to="$(dirname "$registry_file")" "$disk_path")
                local escaped_old escaped_new
                escaped_old=$(printf '%s' "$reg_path" | sed 's/[&/\]/\\&/g')
                escaped_new=$(printf '%s' "$new_rel_path" | sed 's/[&/\]/\\&/g')
                sed -i "s|$(printf '%s' "$reg_path" | sed 's/[|]/\\|/g')|$(printf '%s' "$new_rel_path" | sed 's/[|]/\\|/g')|g" "$registry_file"
                echo -e "  ${GREEN}FIX${NC}: updated path for '${reg_name}' in $(basename "$registry_file"): ${reg_path} -> ${new_rel_path}"
            fi
        fi
    done < "$reg_tmp"

    # Fix domain READMEs (only for src/ artifacts)
    local src_dir="$REPO_ROOT/src/${type_label,,}"
    if [[ -d "$src_dir" ]]; then
        local readme_tmp
        readme_tmp=$(mktemp)
        for domain_dir in "$src_dir"/*/; do
            [[ -d "$domain_dir" ]] || continue
            local readme="${domain_dir}README.md"
            [[ -f "$readme" ]] || continue

            extract_readme_entries "$readme" "$readme_tmp"
            local rel_readme
            rel_readme=$(realpath --relative-to="$REPO_ROOT" "$readme")

            # Remove stale README rows
            while IFS= read -r rname; do
                [[ -z "$rname" ]] && continue
                if [[ -z "${DISK_MAP[$rname]+x}" ]]; then
                    local escaped_name
                    escaped_name=$(printf '%s' "$rname" | sed 's/[]\/$*.^[]/\\&/g')
                    sed -i "/| *\[${escaped_name}\]/d" "$readme"
                    echo -e "  ${GREEN}FIX${NC}: removed stale row '${rname}' from ${rel_readme}"
                fi
            done < "$readme_tmp"

            # Add missing README rows
            for dname in "${!DISK_MAP[@]}"; do
                local dpath="${DISK_MAP[$dname]}"
                local ddir
                ddir="$(dirname "$dpath")"
                if [[ "$artifact_marker" == "SKILL.md" || "$artifact_marker" == "TOOL.md" ]]; then
                    ddir="$(dirname "$ddir")"
                fi
                local norm_domain norm_ddir
                norm_domain=$(realpath -m "$domain_dir")
                norm_ddir=$(realpath -m "$ddir")
                if [[ "$norm_ddir" == "$norm_domain" ]]; then
                    if ! grep -qx "$dname" "$readme_tmp" 2>/dev/null; then
                        local desc intent_or_role rel_link new_row
                        desc=$(extract_field "$dpath" "description")
                        rel_link=$(realpath --relative-to="$domain_dir" "$dpath")

                        case "$type_label" in
                            Skills)
                                intent_or_role=$(extract_field "$dpath" "intent")
                                local skill_dir
                                skill_dir=$(dirname "$rel_link")
                                new_row="| [${dname}](${skill_dir}/) | ${intent_or_role} | ${desc} |"
                                ;;
                            Agents)
                                intent_or_role=$(extract_field "$dpath" "role")
                                new_row="| [${dname}](${rel_link}) | ${intent_or_role} | ${desc} |"
                                ;;
                            Protocols)
                                intent_or_role=$(extract_field "$dpath" "type")
                                new_row="| [${dname}](${rel_link}) | ${intent_or_role} | ${desc} |"
                                ;;
                            Tools)
                                intent_or_role=$(extract_field "$dpath" "action")
                                local tool_dir
                                tool_dir=$(dirname "$rel_link")
                                new_row="| [${dname}](${tool_dir}/) | ${intent_or_role} | ${desc} |"
                                ;;
                        esac

                        echo "$new_row" >> "$readme"
                        echo -e "  ${GREEN}FIX${NC}: added missing row '${dname}' to ${rel_readme}"
                    fi
                fi
            done
        done
        rm -f "$readme_tmp"
    fi

    rm -f "$scan_tmp" "$reg_tmp"
}

# --- README regeneration ---

regen_readmes() {
    local type_label="$1"
    local scan_fn="$2"
    local artifact_marker="$3"

    echo -e "\n${BOLD}${CYAN}[$type_label]${NC}"

    local src_dir="$REPO_ROOT/src/${type_label,,}"
    if [[ ! -d "$src_dir" ]]; then
        echo -e "  ${YELLOW}SKIP${NC}: $src_dir does not exist"
        return 0
    fi

    local scan_tmp
    scan_tmp=$(mktemp)
    $scan_fn "$scan_tmp"
    load_disk_map "$scan_tmp"

    for domain_dir in "$src_dir"/*/; do
        [[ -d "$domain_dir" ]] || continue
        local readme="${domain_dir}README.md"
        local rel_readme
        rel_readme=$(realpath --relative-to="$REPO_ROOT" "$readme")
        local domain_name
        domain_name=$(basename "$domain_dir")

        if [[ ! -f "$readme" ]]; then
            echo -e "  ${YELLOW}SKIP${NC}: no README.md in ${domain_name}/"
            continue
        fi

        # Preserve header: everything before the first table row
        local header=""
        local found_table=false
        while IFS= read -r line; do
            if [[ "$line" =~ ^\| ]] && [[ ! "$found_table" == "true" ]]; then
                found_table=true
                break
            fi
            header+="${line}"$'\n'
        done < "$readme"

        # Build table header based on type
        local table_header separator
        case "$type_label" in
            Skills)
                table_header="| Skill | Intent | Description |"
                separator="|-------|--------|-------------|"
                ;;
            Agents)
                table_header="| Agent | Role | Description |"
                separator="|-------|------|-------------|"
                ;;
            Protocols)
                table_header="| Protocol | Type | Description |"
                separator="|----------|------|-------------|"
                ;;
            Tools)
                table_header="| Tool | Action | Description |"
                separator="|------|--------|-------------|"
                ;;
        esac

        # Collect artifacts in this domain, sorted by name
        local rows=""
        local sorted_names
        sorted_names=$(printf '%s\n' "${!DISK_MAP[@]}" | sort)
        while IFS= read -r dname; do
            [[ -z "$dname" ]] && continue
            local dpath="${DISK_MAP[$dname]}"
            local ddir
            ddir="$(dirname "$dpath")"
            if [[ "$artifact_marker" == "SKILL.md" || "$artifact_marker" == "TOOL.md" ]]; then
                ddir="$(dirname "$ddir")"
            fi
            local norm_domain norm_ddir
            norm_domain=$(realpath -m "$domain_dir")
            norm_ddir=$(realpath -m "$ddir")
            if [[ "$norm_ddir" == "$norm_domain" ]]; then
                local desc intent_or_role rel_link row
                desc=$(extract_field "$dpath" "description")
                rel_link=$(realpath --relative-to="$domain_dir" "$dpath")

                case "$type_label" in
                    Skills)
                        intent_or_role=$(extract_field "$dpath" "intent")
                        local skill_dir
                        skill_dir=$(dirname "$rel_link")
                        row="| [${dname}](${skill_dir}/) | ${intent_or_role} | ${desc} |"
                        ;;
                    Agents)
                        intent_or_role=$(extract_field "$dpath" "role")
                        row="| [${dname}](${rel_link}) | ${intent_or_role} | ${desc} |"
                        ;;
                    Protocols)
                        intent_or_role=$(extract_field "$dpath" "type")
                        row="| [${dname}](${rel_link}) | ${intent_or_role} | ${desc} |"
                        ;;
                    Tools)
                        intent_or_role=$(extract_field "$dpath" "action")
                        local tool_dir
                        tool_dir=$(dirname "$rel_link")
                        row="| [${dname}](${tool_dir}/) | ${intent_or_role} | ${desc} |"
                        ;;
                esac
                rows+="${row}"$'\n'
            fi
        done <<< "$sorted_names"

        # Preserve any content after the table (e.g., ## Layer Chain sections)
        local footer=""
        local past_table=false
        local in_table=false
        while IFS= read -r line; do
            if [[ "$in_table" != "true" ]] && [[ "$line" =~ ^\| ]]; then
                in_table=true
            elif [[ "$in_table" == "true" ]] && [[ ! "$line" =~ ^\| ]]; then
                past_table=true
                in_table=false
            fi
            if [[ "$past_table" == "true" ]]; then
                footer+="${line}"$'\n'
            fi
        done < "$readme"

        # Write regenerated file
        {
            printf '%s' "$header"
            echo "$table_header"
            echo "$separator"
            if [[ -n "$rows" ]]; then
                printf '%s' "$rows"
            fi
            if [[ -n "$footer" ]]; then
                printf '%s' "$footer"
            fi
        } > "$readme"

        local count=0
        if [[ -n "$rows" ]]; then
            count=$(printf '%s' "$rows" | grep -c '^|' || true)
        fi
        echo -e "  ${GREEN}REGEN${NC}: ${rel_readme} (${count} entries)"
    done

    rm -f "$scan_tmp"
}

# --- Shell-comment metadata extraction (for scripts using # @field: value) ---

extract_shell_meta() {
    local file="$1" field="$2"
    grep "^# @${field}:" "$file" 2>/dev/null \
        | head -1 \
        | sed "s/^# @${field}: *//" \
        || true
}

# --- Status extraction with sensible defaults ---

extract_status() {
    local file="$1"
    local s
    s=$(extract_field "$file" "status")
    if [[ -z "$s" ]]; then
        # Scripts have no frontmatter status field; treat as stable if shell metadata present
        if grep -q "^# @name:" "$file" 2>/dev/null; then
            echo "stable"
        else
            echo "draft"
        fi
    else
        echo "$s"
    fi
}

# --- Pathway scan (YAML files) ---

scan_pathways() {
    local outfile="$1"
    > "$outfile"
    while IFS= read -r f; do
        local name
        name=$(grep "^name:" "$f" 2>/dev/null | head -1 | sed 's/^name: *//' | tr -d '"' | tr -d "'")
        [[ -z "$name" ]] && name="$(basename "$f" .yaml)"
        echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/pathways" -name "*.yaml" -type f 2>/dev/null || true)
}

# --- Script scan ---

scan_scripts() {
    local outfile="$1"
    > "$outfile"
    # cortex (repo root, no extension)
    if [[ -f "$REPO_ROOT/cortex" ]]; then
        echo "cortex|$REPO_ROOT/cortex" >> "$outfile"
    fi
    # scripts/*.sh and scripts/*.ps1 — registry uses filename (no extension) as name
    while IFS= read -r f; do
        local name
        name="$(basename "$f")"
        name="${name%.sh}"
        name="${name%.ps1}"
        echo "${name}|${f}" >> "$outfile"
    done < <(find "$REPO_ROOT/scripts" -maxdepth 1 \( -name "*.sh" -o -name "*.ps1" \) -type f 2>/dev/null || true)
}

# --- Description extraction across artifact types ---

extract_description() {
    local file="$1"
    local d
    d=$(extract_field "$file" "description")
    if [[ -z "$d" ]]; then
        d=$(extract_shell_meta "$file" "description")
    fi
    if [[ -z "$d" ]]; then
        # YAML pathway: 'description: "..."'
        d=$(grep "^description:" "$file" 2>/dev/null | head -1 | sed 's/^description: *//' | sed 's/^"//' | sed 's/"$//')
    fi
    echo "$d"
}

# --- Consumer derivation ---
# Builds a global index of all artifacts, then computes a name -> consumers map
# by scanning each artifact's primary file for references to other artifact names.

ARTIFACT_INDEX=""
CONSUMER_MAP=""

build_artifact_index() {
    ARTIFACT_INDEX=$(mktemp)
    local tmp; tmp=$(mktemp)
    scan_skills "$tmp"     && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    scan_agents "$tmp"     && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    scan_protocols "$tmp"  && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    scan_tools "$tmp"      && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    scan_pathways "$tmp"   && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    scan_scripts "$tmp"    && while IFS='|' read -r n p; do [[ -n "$n" ]] && echo "${n}|${p}" >> "$ARTIFACT_INDEX"; done < "$tmp"
    rm -f "$tmp"
}

build_consumer_map() {
    [[ -n "$ARTIFACT_INDEX" && -f "$ARTIFACT_INDEX" ]] || build_artifact_index
    CONSUMER_MAP=$(mktemp)
    > "$CONSUMER_MAP"

    # Read all artifact names (sorted by length descending to match longest first)
    local -a names=()
    while IFS='|' read -r n p; do
        [[ -n "$n" ]] && names+=("$n")
    done < "$ARTIFACT_INDEX"

    # For each artifact's primary file, find which other artifact names it mentions.
    # Record: target_name|consumer_name
    while IFS='|' read -r owner_name owner_path; do
        [[ -z "$owner_name" ]] && continue
        [[ -f "$owner_path" ]] || continue
        for target in "${names[@]}"; do
            [[ "$target" == "$owner_name" ]] && continue
            # Word-boundary match (treat hyphens as part of the word so 'skill' doesn't match 'skill-creator')
            if grep -qE "(^|[^A-Za-z0-9_-])${target}([^A-Za-z0-9_-]|$)" "$owner_path" 2>/dev/null; then
                echo "${target}|${owner_name}" >> "$CONSUMER_MAP"
            fi
        done
    done < "$ARTIFACT_INDEX"
}

lookup_consumers() {
    local name="$1"
    [[ -n "$CONSUMER_MAP" && -f "$CONSUMER_MAP" ]] || { echo "—"; return; }
    local list
    list=$(grep "^${name}|" "$CONSUMER_MAP" 2>/dev/null | cut -d'|' -f2 | sort -u | paste -sd, - | sed 's/,/, /g')
    if [[ -z "$list" ]]; then
        echo "—"
    else
        echo "$list"
    fi
}

# --- Top-level registry regeneration ---

regen_registry() {
    local type_label="$1" registry_file="$2" scan_fn="$3" name_col="$4"

    echo -e "\n${BOLD}${CYAN}[$type_label]${NC}"

    if [[ ! -f "$registry_file" ]]; then
        echo -e "  ${YELLOW}SKIP${NC}: registry file not found: $registry_file"
        return 0
    fi

    local scan_tmp; scan_tmp=$(mktemp)
    $scan_fn "$scan_tmp"

    # Preserve the prose header (everything before first table row)
    local header=""
    while IFS= read -r line; do
        if [[ "$line" =~ ^\| ]]; then break; fi
        header+="${line}"$'\n'
    done < "$registry_file"

    # Build new table
    local registry_dir
    registry_dir="$(dirname "$registry_file")"

    {
        printf '%s' "$header"
        echo "| ${name_col} | Description | Status | Consumers |"
        echo "|------|-------------|--------|-----------|"
        while IFS='|' read -r name path; do
            [[ -z "$name" ]] && continue
            local desc status consumers rel_path
            desc=$(extract_description "$path")
            status=$(extract_status "$path")
            consumers=$(lookup_consumers "$name")
            rel_path=$(realpath --relative-to="$registry_dir" "$path" 2>/dev/null || echo "$path")
            echo "| [${name}](${rel_path}) | ${desc} | ${status} | ${consumers} |"
        done < <(sort "$scan_tmp")
    } > "${registry_file}.tmp"

    mv "${registry_file}.tmp" "$registry_file"

    local count
    count=$(wc -l < "$scan_tmp")
    echo -e "  ${GREEN}REGEN${NC}: $(realpath --relative-to="$REPO_ROOT" "$registry_file") (${count} entries)"

    rm -f "$scan_tmp"
}

# --- Usage ---

usage() {
    cat <<'USAGE'
Usage: sync-registry.sh [command]

Commands:
  status      Show drift between disk and registries/READMEs (default)
  fix         Auto-repair stale entries, path mismatches, and README tables
  readme      Regenerate all domain READMEs from disk state
  registries  Regenerate top-level registry/*.md tables (Status + Consumers from disk)

Options:
  -h, --help    Show this help message

Examples:
  sync-registry.sh              # show drift (same as 'status')
  sync-registry.sh status       # show drift
  sync-registry.sh fix          # auto-repair all drift
  sync-registry.sh readme       # regenerate all domain READMEs
  sync-registry.sh registries   # regenerate top-level registry tables
USAGE
}

# --- Main ---

CMD="${1:-status}"

case "$CMD" in
    -h|--help)
        usage
        exit 0
        ;;
    status)
        echo -e "${BOLD}Checking for drift between disk and registries/READMEs...${NC}"

        check_type "Skills" "$REPO_ROOT/registry/SKILL_REGISTRY.md" scan_skills "SKILL.md"
        check_type "Agents" "$REPO_ROOT/registry/AGENTS_REGISTRY.md" scan_agents "*.md"
        check_type "Protocols" "$REPO_ROOT/registry/PROTOCOL_REGISTRY.md" scan_protocols "*.md"
        check_type "Tools" "$REPO_ROOT/registry/TOOL_REGISTRY.md" scan_tools "TOOL.md"

        echo ""
        echo -e "${BOLD}Summary:${NC} ${STALE_TOTAL} stale registry entries, ${PATH_MISMATCH_TOTAL} path mismatches, ${README_ISSUES_TOTAL} README issues"

        if [[ $((STALE_TOTAL + PATH_MISMATCH_TOTAL + README_ISSUES_TOTAL)) -gt 0 ]]; then
            echo -e "Run ${CYAN}sync-registry.sh fix${NC} to auto-repair."
            exit 1
        fi
        ;;
    fix)
        echo -e "${BOLD}Fixing drift between disk and registries/READMEs...${NC}"

        fix_type "Skills" "$REPO_ROOT/registry/SKILL_REGISTRY.md" scan_skills "SKILL.md"
        fix_type "Agents" "$REPO_ROOT/registry/AGENTS_REGISTRY.md" scan_agents "*.md"
        fix_type "Protocols" "$REPO_ROOT/registry/PROTOCOL_REGISTRY.md" scan_protocols "*.md"
        fix_type "Tools" "$REPO_ROOT/registry/TOOL_REGISTRY.md" scan_tools "TOOL.md"

        echo ""
        echo -e "${GREEN}Done.${NC} Run ${CYAN}sync-registry.sh status${NC} to verify."
        ;;
    readme)
        echo -e "${BOLD}Regenerating domain READMEs from disk state...${NC}"

        regen_readmes "Skills" scan_skills "SKILL.md"
        regen_readmes "Agents" scan_agents "*.md"
        regen_readmes "Protocols" scan_protocols "*.md"
        regen_readmes "Tools" scan_tools "TOOL.md"

        echo ""
        echo -e "${GREEN}Done.${NC}"
        ;;
    registries)
        echo -e "${BOLD}Regenerating top-level registry tables from disk state...${NC}"
        echo -e "Building artifact index and deriving consumer graph..."
        build_artifact_index
        build_consumer_map

        regen_registry "Skills"    "$REPO_ROOT/registry/SKILL_REGISTRY.md"    scan_skills    "Skill"
        regen_registry "Agents"    "$REPO_ROOT/registry/AGENTS_REGISTRY.md"   scan_agents    "Agent"
        regen_registry "Protocols" "$REPO_ROOT/registry/PROTOCOL_REGISTRY.md" scan_protocols "Protocol"
        regen_registry "Tools"     "$REPO_ROOT/registry/TOOL_REGISTRY.md"     scan_tools     "Tool"
        regen_registry "Pathways"  "$REPO_ROOT/registry/PATHWAY_REGISTRY.md"  scan_pathways  "Pathway"
        regen_registry "Scripts"   "$REPO_ROOT/registry/SCRIPT_REGISTRY.md"   scan_scripts   "Script"

        rm -f "$ARTIFACT_INDEX" "$CONSUMER_MAP"
        echo ""
        echo -e "${GREEN}Done.${NC}"
        ;;
    *)
        echo "Unknown command: $CMD"
        usage
        exit 1
        ;;
esac
