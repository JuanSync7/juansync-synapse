# Engineering Principles (mixed)

## Background

When we started this team, we had no shared written principles. Decisions were made in chat, decayed within a week, and were re-litigated the next time a similar question came up. After about three months of this, two of us sat down on a Friday afternoon and tried to articulate what we already believed. The result was rough. We spent another month sanding it. The version below is what survived. It is meant to be read alongside the longer narrative in `docs/history.md`, which captures why each principle is shaped the way it is — context that does not belong in the principles themselves but without which they read as either too obvious or too strange.

We are documenting this in the open because we keep getting asked, and because we'd rather argue with the document than with each other.

## Principles

- We optimize for reversibility before speed.
- We prefer one well-understood failure mode to two clever ones.
- We never merge a change that lacks a written rollback path.
- We hold each other accountable for following these in code review.
- We revise this list when it stops describing how we actually work.
