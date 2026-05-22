"""Version-bump classifier for ai-synapse.

Classifies a diff into one of: 'major' | 'minor' | 'patch'.
Highest triggered category wins (major > minor > patch).

Bump semantics (from synapse package-manager memo, T5):
  Major:  removed/renamed slug, removed CLI flag/subcommand,
          changed `output_type` or `input_type` in SKILLS_REGISTRY.yaml
  Minor:  new artifact (SKILL/AGENT/PROTOCOL/TOOL.md), new registry entry,
          new optional field
  Patch:  body-only edits, EVAL.md, docs, READMEs, scripts

Stdlib only. Python 3.11+.
"""
from __future__ import annotations

import re
import subprocess
from typing import Iterable

ARTIFACT_FILENAMES = ("SKILL.md", "AGENT.md", "PROTOCOL.md", "TOOL.md")
REGISTRY_PATH = "synapse/SKILLS_REGISTRY.yaml"
CORTEX_PATH = "cortex"

# A line in the cortex usage() heredoc looks like:
#     "  <subcommand-with-args>   <description>"
# Two-or-more leading spaces, then a non-space token (the command name),
# then more whitespace, then descriptive text. Removed lines of this shape
# inside the cortex script's diff indicate a subcommand was un-documented.
_CORTEX_SUBCOMMAND_RE = re.compile(r"^-\s{2,}([a-z][a-z0-9-]*)(?:\s|<|$)")


def _is_artifact_file(path: str) -> bool:
    return any(path.endswith("/" + name) or path == name for name in ARTIFACT_FILENAMES)


def _hunk_lines(hunk: str) -> Iterable[str]:
    return hunk.splitlines() if hunk else ()


def _registry_value_changed(hunk: str) -> bool:
    """Detect a *value change* of input_type or output_type in the registry diff.

    A value change means the diff contains both a removed line and an added line
    for the same key (input_type or output_type). A pure addition (only +) is a
    *new* entry, which is minor — not a value change.
    """
    removed = {"input_type": False, "output_type": False}
    added = {"input_type": False, "output_type": False}
    for line in _hunk_lines(hunk):
        # Match leading +/- followed by optional spaces and the key
        m = re.match(r"^([+-])\s*(input_type|output_type)\s*:", line)
        if not m:
            continue
        sign, key = m.group(1), m.group(2)
        if sign == "-":
            removed[key] = True
        else:
            added[key] = True
    return any(removed[k] and added[k] for k in removed)


def _registry_new_entry(hunk: str) -> bool:
    """Detect added registry content (any added lines that aren't matched removals).

    Heuristic: at least one '+' line in the registry hunk that isn't paired with
    a corresponding value change.
    """
    has_added = any(
        line.startswith("+") and not line.startswith("+++")
        for line in _hunk_lines(hunk)
    )
    return has_added


def _cortex_subcommand_removed(hunk: str) -> bool:
    for line in _hunk_lines(hunk):
        if line.startswith("---"):
            continue
        if _CORTEX_SUBCOMMAND_RE.match(line):
            return True
    return False


def classify_bump(diff_files: list[dict]) -> str:
    """Classify a list of diff entries into major/minor/patch.

    diff_files: each dict has keys:
      - path: str
      - status: 'A' | 'M' | 'D' | 'R'
      - old_path: str (for R status)
      - hunk: str (the unified diff content for the file; may be empty for A/D)
    """
    saw_major = False
    saw_minor = False

    for entry in diff_files:
        path = entry.get("path", "")
        status = entry.get("status", "M")
        hunk = entry.get("hunk", "") or ""

        # --- MAJOR triggers ---
        # Deleted artifact file
        if status == "D" and _is_artifact_file(path):
            saw_major = True
            continue
        # Renamed artifact file
        if status == "R" and _is_artifact_file(path):
            saw_major = True
            continue
        # Registry value change (input_type / output_type)
        if path == REGISTRY_PATH and _registry_value_changed(hunk):
            saw_major = True
            # don't `continue` — same file may also have new entries (still major)
        # Cortex subcommand removed from usage() heredoc
        if path == CORTEX_PATH and _cortex_subcommand_removed(hunk):
            saw_major = True

        # --- MINOR triggers ---
        if status == "A" and _is_artifact_file(path):
            saw_minor = True
        if path == REGISTRY_PATH and status in ("A", "M") and _registry_new_entry(hunk):
            # If it was also a value change, major already wins, but still flag minor.
            saw_minor = True

    if saw_major:
        return "major"
    if saw_minor:
        return "minor"
    return "patch"


# ---------------------------------------------------------------------------
# Git-backed entry point
# ---------------------------------------------------------------------------


def _git(args: list[str], repo: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _parse_name_status(raw: str) -> list[tuple[str, str, str | None]]:
    """Parse `git diff --name-status -z` style output.

    Returns list of (status, path, old_path|None).
    Uses non-z output and tab splitting; rename detection produces "R<score>\t<old>\t<new>".
    """
    entries: list[tuple[str, str, str | None]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_field = parts[0]
        # status may be "R100" / "C75" / "A" / "M" / "D"
        code = status_field[0]
        if code == "R" and len(parts) >= 3:
            entries.append(("R", parts[2], parts[1]))
        elif code == "C" and len(parts) >= 3:
            entries.append(("M", parts[2], parts[1]))  # treat copy as modify
        elif len(parts) >= 2:
            entries.append((code, parts[1], None))
    return entries


def classify_diff_against(
    base_ref: str, head_ref: str = "HEAD", repo: str = "."
) -> str:
    """Run `git diff` between base_ref..head_ref and classify the result."""
    name_status = _git(
        ["diff", "--name-status", "-M", f"{base_ref}..{head_ref}"], repo
    )
    entries = _parse_name_status(name_status)

    diff_files: list[dict] = []
    for status, path, old_path in entries:
        hunk = ""
        # Only fetch hunks for files we'll actually inspect content of
        if path == REGISTRY_PATH or path == CORTEX_PATH:
            try:
                hunk = _git(
                    [
                        "diff",
                        "--unified=0",
                        f"{base_ref}..{head_ref}",
                        "--",
                        path,
                    ],
                    repo,
                )
            except subprocess.CalledProcessError:
                hunk = ""
        entry = {"path": path, "status": status, "hunk": hunk}
        if old_path:
            entry["old_path"] = old_path
        diff_files.append(entry)

    return classify_bump(diff_files)
