import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { parsePipelineText, loadPipeline } from '../src/lib/pipeline';
import { resolveRepoRoot } from '../src/repo';

const FIXTURE = `version: 2
built_ins:
  - stage_name: brainstorm
    output_type: design_sketch
registry:
  - name: engineering
    children:
      - name: planning
        skills:
          - name: docs-spec-writer
            pipeline:
              stage_name: spec
              input_type: design_sketch
              output_type: formal_spec
              requires_all: [brainstorm]
              skippable: true
      - name: build
        skills:
          - name: code-builder
            pipeline:
              stage_name: code
              input_type: formal_spec
              output_type: code_diff
              requires_any: [spec]
presets:
  full: [brainstorm, spec, code]
  bugfix: [code]
`;

describe('parsePipelineText', () => {
  it('flattens every skill with a pipeline block into stages', () => {
    const p = parsePipelineText(FIXTURE);
    expect(p.stages.map((s) => s.name).sort()).toEqual(['code-builder', 'docs-spec-writer']);
    const spec = p.stages.find((s) => s.stage_name === 'spec');
    expect(spec?.input_type).toBe('design_sketch');
    expect(spec?.requires_all).toEqual(['brainstorm']);
    expect(spec?.skippable).toBe(true);
    const code = p.stages.find((s) => s.stage_name === 'code');
    expect(code?.requires_any).toEqual(['spec']);
    expect(code?.skippable).toBe(false);
  });

  it('captures built-ins and presets', () => {
    const p = parsePipelineText(FIXTURE);
    expect(p.builtIns).toEqual([{ stage_name: 'brainstorm', output_type: 'design_sketch' }]);
    expect(p.presets.full).toEqual(['brainstorm', 'spec', 'code']);
  });
});

describe('loadPipeline (real registry)', () => {
  it('parses synapse/SKILLS_REGISTRY.yaml: presets.full contains spec', () => {
    const root = resolveRepoRoot();
    const p = loadPipeline(path.join(root, 'synapse', 'SKILLS_REGISTRY.yaml'));
    expect(Array.isArray(p.presets.full)).toBe(true);
    expect(p.presets.full).toContain('spec');
    expect(p.stages.length).toBeGreaterThan(0);
  });
});
