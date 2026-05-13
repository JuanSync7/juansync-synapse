#!/usr/bin/env bash
# synapse-git-dispatch-cr — creates per-artifact feature branches from change requests
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

# ── Usage ───────────────────────────────────────────────────────────
usage() {
    cat <<'USAGE'
Usage: synapse-git-dispatch-cr.sh --date YYYY-MM-DD --slug <session-slug> [--design <path>]

Creates per-artifact feature branches from change request files placed by
synapse-router-artifact-brainstormer's memo-producer.

Options:
  --date     Session date (YYYY-MM-DD) — matches CR files
  --slug     Session slug — matches CR files and derives branch names
  --design   Path to design doc — copied alongside each CR (optional)
  -h, --help Show this help message
USAGE
}

# ── Parse args ──────────────────────────────────────────────────────
SESSION_DATE=""
SESSION_SLUG=""
DESIGN_DOC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --date)   SESSION_DATE="$2"; shift 2 ;;
        --slug)   SESSION_SLUG="$2"; shift 2 ;;
        --design) DESIGN_DOC="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Error: unknown option '$1'" >&2; usage; exit 1 ;;
    esac
done

if [[ -z "$SESSION_DATE" || -z "$SESSION_SLUG" ]]; then
    echo "Error: --date and --slug are required" >&2
    usage
    exit 1
fi

# ── Helpers ─────────────────────────────────────────────────────────

# Extract artifact type from CR file header line:
#   > Artifact type: skill | Memo type: change_request | ...
parse_artifact_type() {
    local cr_file="$1"
    grep -m1 'Artifact type:' "$cr_file" \
        | sed 's/.*Artifact type: *\([a-z]*\).*/\1/' \
        | tr -d '[:space:]'
}

# Extract cr-slug from filename: YYYY-MM-DD-<username>-<slug>.md → <slug>
extract_cr_slug() {
    local filename="$1"
    # Remove .md extension
    filename="${filename%.md}"
    # Remove date prefix (YYYY-MM-DD-)
    filename="${filename#????-??-??-}"
    # Match SESSION_SLUG in the remaining string
    if echo "$filename" | grep -q "$SESSION_SLUG"; then
        echo "$SESSION_SLUG"
    else
        # Fallback: use everything after the first segment as slug
        echo "$filename" | sed 's/^[^-]*-//'
    fi
}

# ── State capture ───────────────────────────────────────────────────
ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
STASHED=false
BRANCHES_CREATED=()
BRANCHES_SKIPPED=()
PUSH_FAILURES=()

# ── Stash if dirty ──────────────────────────────────────────────────
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Stashing uncommitted changes..."
    git stash push -m "synapse-git-dispatch-cr: auto-stash before branch creation"
    STASHED=true
fi

# ── Ensure develop exists locally ───────────────────────────────────
if ! git rev-parse --verify develop >/dev/null 2>&1; then
    if git rev-parse --verify origin/develop >/dev/null 2>&1; then
        echo "Creating local develop from origin/develop..."
        git checkout -q -b develop origin/develop
        git checkout -q "$ORIGINAL_BRANCH"
    else
        echo "Error: develop branch not found locally or on remote" >&2
        if $STASHED; then git stash pop; fi
        exit 1
    fi
fi

# ── Find matching CR files ──────────────────────────────────────────
echo "Scanning for change requests matching date=$SESSION_DATE slug=$SESSION_SLUG..."
echo ""

mapfile -t CR_FILES < <(
    find "$REPO_ROOT" -path "*/change_requests/*${SESSION_DATE}*${SESSION_SLUG}.md" \
        -not -path "*/.git/*" \
        -not -path "*/.claude/*" \
        -not -path "*/.brainstorms/*" \
        2>/dev/null | sort
)

if [[ ${#CR_FILES[@]} -eq 0 ]]; then
    echo "No change requests found for session $SESSION_DATE / $SESSION_SLUG"
    if $STASHED; then git stash pop; fi
    exit 0
fi

echo "Found ${#CR_FILES[@]} change request(s):"
for f in "${CR_FILES[@]}"; do
    echo "  - ${f#$REPO_ROOT/}"
done
echo ""

# ── Capture CR contents before switching branches ───────────────────
# CR files exist on the current branch but may not exist on develop.
# Save content + metadata now, write onto feature branches later.
declare -A CR_CONTENTS
declare -A CR_TYPES
declare -A CR_ARTIFACTS
declare -A CR_SLUGS
declare -A CR_REL_DIRS
declare -A CR_FILENAMES

for cr_file in "${CR_FILES[@]}"; do
    cr_rel="${cr_file#$REPO_ROOT/}"

    # Parse artifact type
    artifact_type="$(parse_artifact_type "$cr_file")" || true
    if [[ -z "$artifact_type" ]]; then
        echo "  WARN  $cr_rel: could not parse artifact type — skipping"
        BRANCHES_SKIPPED+=("$cr_rel (no artifact type)")
        continue
    fi

    # Derive artifact name
    cr_dir="$(dirname "$cr_file")"
    artifact_dir="$(dirname "$cr_dir")"
    artifact_name="$(basename "$artifact_dir")"
    cr_rel_dir="${cr_dir#$REPO_ROOT/}"

    # Extract slug
    cr_filename="$(basename "$cr_file")"
    cr_slug="$(extract_cr_slug "$cr_filename")"

    # Save everything — key by relative path to handle same-name CRs in different artifacts
    CR_CONTENTS["$cr_rel"]="$(cat "$cr_file")"
    CR_TYPES["$cr_rel"]="$artifact_type"
    CR_ARTIFACTS["$cr_rel"]="$artifact_name"
    CR_SLUGS["$cr_rel"]="$cr_slug"
    CR_REL_DIRS["$cr_rel"]="$cr_rel_dir"
    CR_FILENAMES["$cr_rel"]="$cr_filename"
done

# ── Read design doc content if provided ─────────────────────────────
DESIGN_CONTENT=""
if [[ -n "$DESIGN_DOC" && -f "$DESIGN_DOC" ]]; then
    DESIGN_CONTENT="$(cat "$DESIGN_DOC")"
fi

# ── Create branches ─────────────────────────────────────────────────
for cr_key in "${!CR_CONTENTS[@]}"; do
    artifact_type="${CR_TYPES[$cr_key]}"
    artifact_name="${CR_ARTIFACTS[$cr_key]}"
    cr_slug="${CR_SLUGS[$cr_key]}"
    cr_rel_dir="${CR_REL_DIRS[$cr_key]}"
    cr_filename="${CR_FILENAMES[$cr_key]}"

    # Build branch name
    branch_name="feature/${artifact_type}/${artifact_name}/${cr_slug}"

    # Check if branch exists
    if git rev-parse --verify "$branch_name" >/dev/null 2>&1 || \
       git rev-parse --verify "origin/$branch_name" >/dev/null 2>&1; then
        echo "  SKIP  $branch_name (already exists)"
        BRANCHES_SKIPPED+=("$branch_name")
        continue
    fi

    echo "  CREATE  $branch_name"

    # Create branch from develop
    git checkout -q develop
    git checkout -q -b "$branch_name"

    # Write CR file onto the new branch
    mkdir -p "$REPO_ROOT/$cr_rel_dir"
    echo "${CR_CONTENTS[$cr_key]}" > "$REPO_ROOT/$cr_rel_dir/$cr_filename"
    git add "$REPO_ROOT/$cr_rel_dir/$cr_filename"

    # Copy design doc if provided
    if [[ -n "$DESIGN_CONTENT" ]]; then
        username="$(git config user.name | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
        design_dest="$REPO_ROOT/$cr_rel_dir/${SESSION_DATE}-${username}-${cr_slug}-design.md"

        # Collision check
        if [[ -f "$design_dest" ]]; then
            counter=2
            base="${design_dest%.md}"
            while [[ -f "${base}-${counter}.md" ]]; do
                ((counter++))
            done
            design_dest="${base}-${counter}.md"
        fi

        echo "$DESIGN_CONTENT" > "$design_dest"
        git add "$design_dest"
    fi

    # Commit
    git commit -q -m "chore: add change request for ${artifact_name}

CR: ${cr_filename}
Session: ${SESSION_DATE}-${SESSION_SLUG}"

    # Push (don't fail if no remote)
    if git push -u origin "$branch_name" 2>/dev/null; then
        BRANCHES_CREATED+=("$branch_name")
    else
        BRANCHES_CREATED+=("$branch_name (local only)")
        PUSH_FAILURES+=("$branch_name")
    fi

    # Return to develop
    git checkout -q develop
done

# ── Return to original branch ──────────────────────────────────────
git checkout -q "$ORIGINAL_BRANCH"

# ── Pop stash ───────────────────────────────────────────────────────
if $STASHED; then
    echo ""
    echo "Restoring stashed changes..."
    git stash pop
fi

# ── Summary ─────────────────────────────────────────────────────────
echo ""
echo "=== Synapse CR Dispatcher Summary ==="
echo ""

if [[ ${#BRANCHES_CREATED[@]} -gt 0 ]]; then
    echo "Created (${#BRANCHES_CREATED[@]}):"
    for b in "${BRANCHES_CREATED[@]}"; do
        echo "  + $b"
    done
fi

if [[ ${#BRANCHES_SKIPPED[@]} -gt 0 ]]; then
    echo ""
    echo "Skipped (${#BRANCHES_SKIPPED[@]}):"
    for b in "${BRANCHES_SKIPPED[@]}"; do
        echo "  ~ $b"
    done
fi

if [[ ${#PUSH_FAILURES[@]} -gt 0 ]]; then
    echo ""
    echo "Push failed (branches exist locally — push manually):"
    for b in "${PUSH_FAILURES[@]}"; do
        echo "  ! $b"
    done
fi

echo ""
echo "Done. Next: switch to a feature branch and start implementing."
