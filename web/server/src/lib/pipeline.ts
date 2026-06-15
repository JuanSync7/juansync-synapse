import fs from 'node:fs';
import { parse as parseYaml } from 'yaml';
import type { PipelineBuiltIn, PipelineData, PipelineStage } from '../../../shared/types';

interface PipelineBlock {
  stage_name?: unknown;
  input_type?: unknown;
  output_type?: unknown;
  requires_all?: unknown;
  requires_any?: unknown;
  skippable?: unknown;
}

interface RegistryNode {
  name?: unknown;
  children?: unknown;
  skills?: unknown;
  pipeline?: unknown;
}

/**
 * Parse the pipeline registry from raw YAML text. The registry is a nested tree
 * under `registry:` where intermediate nodes carry `children` and leaf nodes
 * carry `skills`; only skills with a `pipeline:` block are routable stages. We
 * recurse the whole tree and flatten those into a single stage list because the
 * tree shape is an authoring convenience, not a routing concern — the
 * orchestrator and the UI both want a flat stage graph.
 */
export function parsePipelineText(text: string): PipelineData {
  let doc: unknown;
  try {
    doc = parseYaml(text);
  } catch {
    doc = null;
  }
  const root = (doc !== null && typeof doc === 'object' ? doc : {}) as Record<string, unknown>;

  const builtIns: PipelineBuiltIn[] = asArray(root.built_ins).map((b) => {
    const o = (b ?? {}) as Record<string, unknown>;
    return { stage_name: str(o.stage_name) ?? '', output_type: str(o.output_type) };
  });

  const stages: PipelineStage[] = [];
  for (const node of asArray(root.registry)) {
    collectStages(node as RegistryNode, stages);
  }

  const presets: Record<string, string[]> = {};
  const rawPresets = root.presets;
  if (rawPresets !== null && typeof rawPresets === 'object' && !Array.isArray(rawPresets)) {
    for (const [k, v] of Object.entries(rawPresets as Record<string, unknown>)) {
      presets[k] = asArray(v).map((x) => String(x));
    }
  }

  return { builtIns, stages, presets };
}

/** Load and parse the pipeline registry from a file path. */
export function loadPipeline(filePath: string): PipelineData {
  return parsePipelineText(fs.readFileSync(filePath, 'utf8'));
}

function collectStages(node: RegistryNode, out: PipelineStage[]): void {
  if (node === null || typeof node !== 'object') return;

  const pipeline = node.pipeline;
  if (pipeline !== null && typeof pipeline === 'object' && !Array.isArray(pipeline)) {
    const p = pipeline as PipelineBlock;
    out.push({
      name: str(node.name) ?? '',
      stage_name: str(p.stage_name) ?? '',
      input_type: str(p.input_type),
      output_type: str(p.output_type),
      requires_all: asArray(p.requires_all).map((x) => String(x)),
      requires_any: asArray(p.requires_any).map((x) => String(x)),
      skippable: p.skippable === true,
    });
  }

  for (const child of asArray(node.children)) {
    collectStages(child as RegistryNode, out);
  }
  for (const skill of asArray(node.skills)) {
    collectStages(skill as RegistryNode, out);
  }
}

function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function str(v: unknown): string | null {
  return typeof v === 'string' ? v : null;
}
