"""Tests for scripts/lib/version_bump.classify_bump and classify_diff_against."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Make scripts/lib importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import version_bump  # noqa: E402


# ---------------------------------------------------------------------------
# Unit tests using synthetic diff dicts
# ---------------------------------------------------------------------------


def test_patch_readme_only():
    diff = [{"path": "README.md", "status": "M", "hunk": "+ some line\n- old line\n"}]
    assert version_bump.classify_bump(diff) == "patch"


def test_patch_skill_body_change():
    diff = [
        {
            "path": "synapse/skills/foo/SKILL.md",
            "status": "M",
            "hunk": "+ This is new body text.\n- Old body text.\n",
        }
    ]
    assert version_bump.classify_bump(diff) == "patch"


def test_patch_eval_md_change():
    diff = [
        {
            "path": "synapse/skills/foo/EVAL.md",
            "status": "M",
            "hunk": "+ new criterion\n",
        }
    ]
    assert version_bump.classify_bump(diff) == "patch"


def test_minor_new_skill_md():
    diff = [
        {
            "path": "synapse/skills/new-skill/SKILL.md",
            "status": "A",
            "hunk": "+ all new content\n",
        }
    ]
    assert version_bump.classify_bump(diff) == "minor"


def test_minor_new_agent_md():
    diff = [
        {
            "path": "synapse/agents/new-agent/AGENT.md",
            "status": "A",
            "hunk": "+ content\n",
        }
    ]
    assert version_bump.classify_bump(diff) == "minor"


def test_minor_new_protocol_md():
    diff = [
        {"path": "synapse/protocols/new-proto/PROTOCOL.md", "status": "A", "hunk": "+ x\n"}
    ]
    assert version_bump.classify_bump(diff) == "minor"


def test_minor_new_tool_md():
    diff = [{"path": "synapse/tools/new-tool/TOOL.md", "status": "A", "hunk": "+ x\n"}]
    assert version_bump.classify_bump(diff) == "minor"


def test_minor_new_registry_entry():
    # New entry added (only + lines for a stage block, no removals)
    hunk = """\
+  - stage_name: new-stage
+    input_type: design
+    output_type: implementation
"""
    diff = [{"path": "synapse/SKILLS_REGISTRY.yaml", "status": "M", "hunk": hunk}]
    assert version_bump.classify_bump(diff) == "minor"


def test_major_skill_md_deleted():
    diff = [
        {"path": "synapse/skills/old/SKILL.md", "status": "D", "hunk": "- gone\n"},
    ]
    assert version_bump.classify_bump(diff) == "major"


def test_major_agent_md_deleted():
    diff = [{"path": "synapse/agents/old/AGENT.md", "status": "D", "hunk": "- gone\n"}]
    assert version_bump.classify_bump(diff) == "major"


def test_major_skill_md_renamed():
    # Rename detected via R status (git rename)
    diff = [
        {
            "path": "synapse/skills/new-name/SKILL.md",
            "status": "R",
            "old_path": "synapse/skills/old-name/SKILL.md",
            "hunk": "",
        }
    ]
    assert version_bump.classify_bump(diff) == "major"


def test_major_skill_renamed_via_d_plus_a():
    # Rename detected as D + A of SKILL.md files (no R)
    diff = [
        {"path": "synapse/skills/old-name/SKILL.md", "status": "D", "hunk": "- gone\n"},
        {"path": "synapse/skills/new-name/SKILL.md", "status": "A", "hunk": "+ new\n"},
    ]
    # When both happen in same diff, it's "major" (deletion alone qualifies)
    assert version_bump.classify_bump(diff) == "major"


def test_major_output_type_value_changed():
    hunk = """\
   - stage_name: design
-    output_type: design_doc
+    output_type: design_artifact
     input_type: spec
"""
    diff = [{"path": "synapse/SKILLS_REGISTRY.yaml", "status": "M", "hunk": hunk}]
    assert version_bump.classify_bump(diff) == "major"


def test_major_input_type_value_changed():
    hunk = """\
-    input_type: design_doc
+    input_type: design_artifact
"""
    diff = [{"path": "synapse/SKILLS_REGISTRY.yaml", "status": "M", "hunk": hunk}]
    assert version_bump.classify_bump(diff) == "major"


def test_major_cortex_subcommand_removed():
    # A line documenting a subcommand inside usage() heredoc was removed.
    # Classifier looks at cortex script diff for removed lines starting with "  <word>"
    # within the heredoc.
    hunk = """\
   list                                List installed synapses
-  available                           Show all available synapses
   pathway <subcommand>                Manage pathways
"""
    diff = [{"path": "cortex", "status": "M", "hunk": hunk}]
    assert version_bump.classify_bump(diff) == "major"


def test_highest_wins_minor_plus_major():
    diff = [
        {"path": "synapse/skills/new/SKILL.md", "status": "A", "hunk": "+ x\n"},
        {"path": "synapse/skills/old/SKILL.md", "status": "D", "hunk": "- y\n"},
    ]
    assert version_bump.classify_bump(diff) == "major"


def test_highest_wins_patch_plus_minor():
    diff = [
        {"path": "README.md", "status": "M", "hunk": "+ doc\n"},
        {"path": "synapse/skills/new/SKILL.md", "status": "A", "hunk": "+ x\n"},
    ]
    assert version_bump.classify_bump(diff) == "minor"


def test_empty_diff_is_patch():
    assert version_bump.classify_bump([]) == "patch"


# ---------------------------------------------------------------------------
# Integration test: real git repo
# ---------------------------------------------------------------------------


def _run(cmd, cwd, env=None):
    return subprocess.run(
        cmd, cwd=cwd, check=True, capture_output=True, text=True, env=env
    )


def _git_env():
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "t@t"
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "t@t"
    return env


def test_classify_diff_against_integration(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = _git_env()
    _run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env)
    # Initial commit
    (repo / "README.md").write_text("hi\n")
    _run(["git", "add", "."], cwd=repo, env=env)
    _run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env)
    base = _run(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()

    # Add a new SKILL.md → minor
    skill_dir = repo / "synapse" / "skills" / "new-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# new skill\n")
    _run(["git", "add", "."], cwd=repo, env=env)
    _run(["git", "commit", "-q", "-m", "add skill"], cwd=repo, env=env)

    result = version_bump.classify_diff_against(base, "HEAD", str(repo))
    assert result == "minor"

    # Now delete the SKILL.md → major (against original base)
    (skill_dir / "SKILL.md").unlink()
    _run(["git", "add", "-A"], cwd=repo, env=env)
    _run(["git", "commit", "-q", "-m", "remove skill"], cwd=repo, env=env)

    # Diff base→HEAD: README untouched, SKILL.md added then removed = no net change
    # but commit history shows D, so we test against the "add skill" commit instead
    add_sha = _run(
        ["git", "rev-parse", "HEAD~1"], cwd=repo, env=env
    ).stdout.strip()
    result2 = version_bump.classify_diff_against(add_sha, "HEAD", str(repo))
    assert result2 == "major"
