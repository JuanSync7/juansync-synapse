import { afterEach, describe, expect, it } from 'vitest';
import {
  buildIndex,
  invalidateCache,
  matchRegistryRow,
  resolvePathway,
} from '../src/lib/crawler';
import { resolveRepoRoot } from '../src/repo';

const root = resolveRepoRoot();

afterEach(() => invalidateCache());

describe('matchRegistryRow', () => {
  const table = `| Skill | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [docs-spec-writer](../src/skills/docs/docs-spec-writer/SKILL.md) | Writes specs | stable | — |
| [other-skill](../x/SKILL.md) | Other | draft | — |
`;
  it('matches the row whose first column slug equals the target', () => {
    const row = matchRegistryRow(table, 'docs-spec-writer');
    expect(row).not.toBeNull();
    expect(row?.Description).toBe('Writes specs');
    expect(row?.Status).toBe('stable');
  });
  it('returns null when no row matches', () => {
    expect(matchRegistryRow(table, 'nope')).toBeNull();
  });
});

describe('buildIndex (real repo)', () => {
  it('classifies an adopter skill under src/ as layer=addon and detects its EVAL', () => {
    // Structural, not slug-specific: adopter slugs migrate across branches, so
    // assert the crawler's layer classification + eval detection on whatever
    // addon skill(s) exist rather than a hardcoded name.
    const idx = buildIndex(root);
    const addonSkills = idx.filter((a) => a.class === 'skill' && a.layer === 'addon');
    expect(addonSkills.length).toBeGreaterThan(0);
    expect(addonSkills.some((a) => a.hasEval)).toBe(true);
  });

  it('finds the base skill synapse-router-artifact-creator with layer=base', () => {
    const idx = buildIndex(root);
    const s = idx.find((a) => a.slug === 'synapse-router-artifact-creator');
    expect(s?.layer).toBe('base');
  });

  it('indexes tools (TOOL.md artifacts)', () => {
    const idx = buildIndex(root);
    expect(idx.filter((a) => a.class === 'tool').length).toBeGreaterThan(0);
  });

  it('indexes at least 30 skills', () => {
    const idx = buildIndex(root);
    expect(idx.filter((a) => a.class === 'skill').length).toBeGreaterThanOrEqual(30);
  });

  it('excludes README.md and *.eval.md from agents/protocols', () => {
    const idx = buildIndex(root);
    expect(idx.some((a) => a.slug.toLowerCase() === 'readme')).toBe(false);
    expect(idx.some((a) => a.path.endsWith('.eval.md'))).toBe(false);
  });

  it('excludes change_requests from protocols', () => {
    const idx = buildIndex(root);
    expect(idx.some((a) => a.path.includes('change_requests/'))).toBe(false);
  });
});

describe('resolvePathway (real repo)', () => {
  it('resolves synapse-skill to a non-empty skills array', () => {
    const r = resolvePathway(root, 'synapse-skill');
    expect(r).not.toBeNull();
    expect(Array.isArray(r?.skills)).toBe(true);
    expect((r?.skills.length ?? 0)).toBeGreaterThan(0);
  });
});
