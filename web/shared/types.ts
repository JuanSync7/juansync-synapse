// Shared types used by both server and client (DESIGN.md: web/shared).
// Slice S3 adds Artifact, ArtifactDetail, Criterion, EvalGroups, EvalData,
// Companion, PipelineData, Counts. Keep client-compatible: no node-only types.

/** The five synapse artifact classes the crawler indexes (FR1.1). */
export type ArtifactClass = 'skill' | 'agent' | 'protocol' | 'tool' | 'pathway';

/** Which tree an artifact lives in: synapse/ (base), src/ (addon), external/. */
export type Layer = 'base' | 'addon' | 'external';

/** A single artifact discovered by the crawler (FR1.1). */
export interface Artifact {
  slug: string;
  class: ArtifactClass;
  layer: Layer;
  /** Repo-relative POSIX path to the artifact's defining file. */
  path: string;
  domain: string | null;
  status: string;
  description: string | null;
  /** Full parsed frontmatter object (verbatim). */
  frontmatter: Record<string, unknown>;
  hasEval: boolean;
}

/** Per-class totals, always reflecting the unfiltered index (FR1.1). */
export interface Counts {
  skill: number;
  agent: number;
  protocol: number;
  tool: number;
  pathway: number;
}

/** Response shape for GET /api/artifacts. */
export interface ArtifactListResponse {
  items: Artifact[];
  counts: Counts;
}

/** A single parsed EVAL.md checklist criterion (FR2). */
export interface Criterion {
  id: string;
  text: string;
  checked: boolean;
}

/** EVAL criteria grouped by id prefix (EVAL-E / EVAL-O / other). */
export interface EvalGroups {
  execution: Criterion[];
  output: Criterion[];
  other: Criterion[];
}

/** Parsed EVAL.md payload attached to an artifact detail. */
export interface EvalData {
  raw: string;
  groups: EvalGroups;
  isPlaceholder: boolean;
}

/** A companion file (references/, templates/, schemas, cli) of an artifact. */
export interface Companion {
  name: string;
  /** Repo-relative POSIX path. */
  path: string;
  kind: 'reference' | 'template' | 'schema' | 'cli' | 'other';
}

/** Response shape for GET /api/artifacts/:class/:slug. */
export interface ArtifactDetail {
  item: Artifact;
  /** Raw markdown (or raw YAML for pathways). */
  body: string;
  eval: EvalData | null;
  companions: Companion[];
  /** Parsed registry table row for this slug, if present. */
  registryRow: Record<string, string> | null;
  /** For pathways: flattened inherits-resolved bundle, else null. */
  pathwayResolved: ResolvedPathway | null;
}

/** A pathway with its `inherits:` chain flattened (FR1.4). */
export interface ResolvedPathway {
  name: string;
  skills: string[];
  agents: string[];
  protocols: string[];
  tools: string[];
}

/** One pipeline stage entry, flattened from the registry tree (FR4.2). */
export interface PipelineStage {
  name: string;
  stage_name: string;
  input_type: string | null;
  output_type: string | null;
  requires_all: string[];
  requires_any: string[];
  skippable: boolean;
}

/** A built-in stage executed directly by the orchestrator. */
export interface PipelineBuiltIn {
  stage_name: string;
  output_type: string | null;
}

/** Response shape for GET /api/pipeline (FR4.2). */
export interface PipelineData {
  builtIns: PipelineBuiltIn[];
  stages: PipelineStage[];
  presets: Record<string, string[]>;
}

// --- Registry & taxonomy editing (FR3) -------------------------------------

/** Parsed pipe-table from a registry file (mirror of server lib MdTable). */
export interface RegistryTable {
  headers: string[];
  rows: string[][];
}

/** One entry in the registry-file listing (GET /api/registry). */
export interface RegistryFile {
  name: string;
  path: string;
  kind: 'registry' | 'vocabulary';
}

/** Response shape for GET /api/registry/:name. */
export interface RegistryDetail {
  name: string;
  raw: string;
  /** Parsed table, or null when the file is not a single clean table. */
  table: RegistryTable | null;
}

/** One entry in the taxonomy-file listing (GET /api/taxonomy). */
export interface TaxonomyFile {
  name: string;
  path: string;
  kind: 'taxonomy' | 'vocabulary';
}

/** Response shape for GET /api/taxonomy/:name. */
export interface TaxonomyDetail {
  name: string;
  raw: string;
}

// --- Scripts control panel (FR8) -------------------------------------------

/** A shell script in scripts/*.sh, parsed from its `# @key:` comment head. */
export interface ScriptMeta {
  kind: 'script';
  name: string;
  description: string | null;
  audience: string | null;
  action: string | null;
  scope: string | null;
  /** Repo-relative POSIX path to the .sh file. */
  path: string;
  /** Contents of docs/cli/<name>.md if present, else null. */
  doc: string | null;
}

/** A cortex python-CLI command group documented under docs/cli without a .sh. */
export interface CliCommandMeta {
  kind: 'cli-command';
  name: string;
  doc: string;
}

/** Response shape for GET /api/scripts (FR8.1). */
export interface ScriptsResponse {
  scripts: ScriptMeta[];
  cliCommands: CliCommandMeta[];
}

/** Result of an allow-listed command run (FR8.3, NFR5). */
export interface ExecResult {
  command: string;
  stdout: string;
  stderr: string;
  exitCode: number;
}

// --- Memo system (FR5) -----------------------------------------------------

/** How a memo's `executed` flag was resolved (resolution priority order). */
export type MemoExecutedSource = 'frontmatter' | 'meta' | 'default';

/** A memo: an actionable artifact-creation record (FR5.1). */
export interface Memo {
  /** Stable, path-derived id (`/`→`__`, `.md` stripped, url-safe). */
  id: string;
  /** First `# ` heading, or the filename. */
  title: string;
  /** `brainstorm:<slug>` or `change_requests:<dir>`. */
  source: string;
  /** Brainstorm slug when from a session, else null. */
  session: string | null;
  /** Artifact type from the meta.yaml entry or inferred from the path. */
  artifactType: string | null;
  /** Resolved executed flag (see resolution order, FR5.1). */
  executed: boolean;
  /** Which rule decided `executed`. */
  executedSource: MemoExecutedSource;
  /** Repo-relative POSIX path, or null when the memo file doesn't exist yet. */
  path: string | null;
  /** YYYY-MM-DD from the filename date prefix, else null. */
  createdDate: string | null;
}

/** Per-status memo totals (FR5.1). */
export interface MemoCounts {
  total: number;
  executed: number;
  pending: number;
}

/** Response shape for GET /api/memos (FR5.1). */
export interface MemoListResponse {
  memos: Memo[];
  counts: MemoCounts;
}

/** Response shape for GET /api/memos/:id (FR5.1) — memo plus raw body. */
export interface MemoDetail {
  memo: Memo;
  /** Raw markdown body (the whole file, verbatim). */
  body: string;
}

// --- Framework page (FR4) --------------------------------------------------

/** A base (synapse/) artifact summarized for the framework page. */
export interface FrameworkArtifact {
  slug: string;
  class: ArtifactClass;
  description: string | null;
  /** A short role hint (frontmatter role/domain), else null. */
  role: string | null;
}

/** Base artifacts grouped by class (FR4.1). */
export interface FrameworkGroups {
  skills: FrameworkArtifact[];
  agents: FrameworkArtifact[];
  protocols: FrameworkArtifact[];
  tools: FrameworkArtifact[];
}

/** One lifecycle step, mapped to its actual base skill slug when matched. */
export interface LifecycleStep {
  /** Conceptual stage label (brainstormer, creator, …). */
  label: string;
  /** Resolved base skill slug, or null when no base skill matches. */
  slug: string | null;
}

/** Response shape for GET /api/framework (FR4.1). */
export interface FrameworkData {
  groups: FrameworkGroups;
  lifecycle: LifecycleStep[];
}

// --- Headless claude sessions (FR6) ----------------------------------------

/** Lifecycle status of a headless claude session. */
export type SessionStatus = 'running' | 'done' | 'error';

/** The event types emitted by the claude stream-json driver. */
export type SessionEventType =
  | 'system'
  | 'assistant'
  | 'user'
  | 'result'
  | 'error'
  | 'stderr'
  | 'exit';

/** One parsed event from the claude stream-json transcript. */
export interface SessionEvent {
  type: SessionEventType;
  /** The raw parsed JSON line (or a wrapper for stderr/exit/error). */
  data: unknown;
}

/** Persisted metadata for a session (`<id>.meta.json`, FR6.4). */
export interface SessionMeta {
  id: string;
  /** Claude's own session id (from system/result lines), filled when known. */
  claudeSessionId: string | null;
  status: SessionStatus;
  /** ISO timestamp the session started. */
  startedAt: string;
  /** The effective prompt sent to claude (skill-prefixed). */
  prompt: string;
  /** A short human title (derived from the first message). */
  title: string;
}

/** Response shape for GET /api/sessions — the session list (FR6.3). */
export interface SessionListResponse {
  sessions: SessionMeta[];
}

/** Response shape for GET /api/sessions/:id — meta + replayed transcript. */
export interface SessionDetail {
  meta: SessionMeta;
  events: SessionEvent[];
}

// --- Creator end-to-end runs (FR7) -----------------------------------------

/** Lifecycle status of a creator run. */
export type RunStatus = 'running' | 'succeeded' | 'failed';

/**
 * One created/modified path detected from the git porcelain diff taken across a
 * run. `status` is the two-letter porcelain code (e.g. `A`, `M`, `??`).
 */
export interface CreatedPath {
  /** Repo-relative POSIX path. */
  path: string;
  /** Porcelain status code, trimmed (`A`, `M`, `??`, `R`, …). */
  status: string;
  /** Inferred artifact class + slug when the path is a SKILL.md/TOOL.md/etc. */
  artifact: { class: ArtifactClass; slug: string } | null;
}

/** The post-run verification payload (git diff + validate result). */
export interface RunVerification {
  createdPaths: CreatedPath[];
  validate: ExecResult;
}

/** Persisted metadata for a creator run (`runs/<id>.meta.json`, FR7.3). */
export interface RunMeta {
  id: string;
  kind: 'creator-run';
  /** The memo this run was launched against. */
  memoId: string;
  /** Repo-relative POSIX path to the memo file. */
  memoPath: string;
  status: RunStatus;
  /** ISO timestamp the run started. */
  startedAt: string;
  /** The underlying claude session id (so the transcript can be read). */
  sessionId: string;
  /** Filled on completion: paths the run created/modified (git diff). */
  createdPaths?: CreatedPath[];
  /** Filled on completion: the `./cortex validate` result. */
  validate?: ExecResult;
}

/** Response shape for GET /api/runs — the run list (FR7.3). */
export interface RunListResponse {
  runs: RunMeta[];
}

/** Response shape for GET /api/runs/:id — meta + transcript + verification. */
export interface RunDetail {
  meta: RunMeta;
  events: SessionEvent[];
  /** Present once the run has completed verification. */
  verification: RunVerification | null;
}
