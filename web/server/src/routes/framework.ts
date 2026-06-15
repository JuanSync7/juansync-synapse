// Framework page API (FR4.1). Crawls the artifact index, keeps only base
// (synapse/) items, groups them by class, and emits the creation-lifecycle
// ordering. The lifecycle is a fixed conceptual sequence (brainstormer →
// creator → eval-writer → improver → gatekeeper → suite-validator); each step
// is resolved to the actual base skill slug whose name contains the step's
// matcher, so the client can deep-link to /artifact/skill/<slug>. A step with
// no matching base skill resolves to slug:null (rendered as a non-link node)
// rather than dropping — the lifecycle shape is the teaching aid.
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import type {
  FrameworkArtifact,
  FrameworkData,
  FrameworkGroups,
  LifecycleStep,
} from '../../../shared/types';
import { getIndex } from '../lib/crawler';

// Each lifecycle step + the substring used to find its base skill slug.
const LIFECYCLE: ReadonlyArray<readonly [label: string, matcher: string]> = [
  ['brainstormer', 'brainstormer'],
  ['creator', 'creator'],
  ['eval-writer', 'eval-writer'],
  ['improver', 'improver'],
  ['gatekeeper', 'gatekeeper'],
  ['suite-validator', 'suite-validator'],
];

export function frameworkRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  router.get('/', (_req, res) => {
    const base = getIndex(repoRoot).filter((a) => a.layer === 'base');

    const groups: FrameworkGroups = { skills: [], agents: [], protocols: [], tools: [] };
    for (const a of base) {
      const entry: FrameworkArtifact = {
        slug: a.slug,
        class: a.class,
        description: a.description,
        role: roleOf(a.frontmatter) ?? a.domain,
      };
      if (a.class === 'skill') groups.skills.push(entry);
      else if (a.class === 'agent') groups.agents.push(entry);
      else if (a.class === 'protocol') groups.protocols.push(entry);
      else if (a.class === 'tool') groups.tools.push(entry);
      // pathways are not a framework artifact class on this page.
    }
    for (const key of ['skills', 'agents', 'protocols', 'tools'] as const) {
      groups[key].sort((x, y) => x.slug.localeCompare(y.slug));
    }

    const baseSkillSlugs = groups.skills.map((s) => s.slug);
    const lifecycle: LifecycleStep[] = LIFECYCLE.map(([label, matcher]) => ({
      label,
      slug: baseSkillSlugs.find((slug) => slug.includes(matcher)) ?? null,
    }));

    const payload: FrameworkData = { groups, lifecycle };
    res.json(payload);
  });

  return router;
}

function roleOf(fm: Record<string, unknown>): string | null {
  const role = fm.role;
  return typeof role === 'string' ? role : null;
}
