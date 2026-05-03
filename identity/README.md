# Identity

Personal identity files consumed by AI agents across all tools. These define **who you are** — separate from what agents can do (skills) or how they evaluate decisions in a specific pipeline (stakeholder-reviewer skill).

## Files

| File | Purpose | Installed to |
|------|---------|--------------|
| `SOUL.template.md` | Blank skeleton with guidance for creating your own SOUL.md | *(not installed — copy to `SOUL.md` and customize)* |
| `STAKEHOLDER.template.md` | Blank skeleton with guidance for creating your own STAKEHOLDER.md | *(not installed — copy to `STAKEHOLDER.md` and customize)* |

The framework distribution does not ship a pre-filled `SOUL.md` or `STAKEHOLDER.md` — those are personal artifacts each adopter authors for themselves.

## Two Consumption Modes

SOUL.md serves agents in two ways from the same file:

- **Emulation (Job 1):** Agent acts like you — predicts your preferences, writes in your voice, reviews like you would.
- **Compensation (Job 2):** Agent challenges your blind spots — pushes back where you're weak, is thorough where you're impatient, anchors you when you drift.

The soul is descriptive (neutral facts about who you are). The consuming agent or skill decides which mode to use.

## Installation

```bash
./scripts/install.sh identity
```

This creates symlinks:
- `identity/SOUL.md` → `~/.claude/SOUL.md`
- `identity/STAKEHOLDER.md` → `~/.claude/stakeholder.md`

If `~/.claude/stakeholder.md` already exists as a regular file, back it up and remove it first — the installer won't overwrite existing files.

## Creating Your Own SOUL.md

1. Copy `SOUL.template.md` to `SOUL.md`
2. Fill in each section following the guidance comments
3. Run through the quality checklist at the bottom
4. Run `./scripts/install.sh identity` to symlink it

**Quality bar:** An agent reading your SOUL.md should be able to predict your stance on a new topic you haven't explicitly covered.

## Relationship to Other Files

| File | Scope | Always loaded? | Purpose |
|------|-------|----------------|---------|
| `SOUL.md` | Global identity | Yes (via `~/.claude/CLAUDE.md` reference) | Who you are |
| `stakeholder.md` | Decision gate | No (loaded by stakeholder-reviewer skill) | How you evaluate decisions |
| `CLAUDE.md` (global) | Behavioral instructions | Yes (auto-loaded by Claude Code) | How Claude should interact with you |
| `MEMORY.md` | Temporal context | Yes (auto-loaded) | What's happening now, recent learnings |

SOUL.md and stakeholder.md are **independent** — they overlap in values but serve different consumers at different times. Neither derives from the other.

## Multi-Agent Use (Future)

In multi-agent brainstorm rooms, each agent reads only its own person's SOUL.md — preserving diversity. Agents can swap between Job 1 (emulate) and Job 2 (compensate) mid-session based on what the task needs.
