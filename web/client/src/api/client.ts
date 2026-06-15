// Typed fetch wrapper for the synapse-web API (FR1.3, FR4.2, FR9).
// All artifact/pipeline reads funnel through here so pages never touch fetch
// directly — keeps error handling and the API base in one place.
import type {
  ArtifactClass,
  ArtifactDetail,
  ArtifactListResponse,
  ExecResult,
  FrameworkData,
  MemoDetail,
  MemoListResponse,
  PipelineData,
  RegistryDetail,
  RegistryFile,
  RunDetail,
  RunListResponse,
  ScriptsResponse,
  SessionDetail,
  SessionListResponse,
  TaxonomyDetail,
  TaxonomyFile,
} from '../../../shared/types';

export interface ListParams {
  class?: ArtifactClass;
  q?: string;
  layer?: string;
  domain?: string;
}

/** Thrown on any non-2xx response; carries the server's JSON `error` message. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    // Surface the server's structured error when present; fall back to status text.
    let message = res.statusText || `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body && typeof body.error === 'string') message = body.error;
    } catch {
      // non-JSON error body — keep the status-derived message
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

export function listArtifacts(params: ListParams = {}): Promise<ArtifactListResponse> {
  const qs = new URLSearchParams();
  if (params.class) qs.set('class', params.class);
  if (params.q) qs.set('q', params.q);
  if (params.layer) qs.set('layer', params.layer);
  if (params.domain) qs.set('domain', params.domain);
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  return getJson<ArtifactListResponse>(`/api/artifacts${suffix}`);
}

export function getArtifact(cls: ArtifactClass, slug: string): Promise<ArtifactDetail> {
  return getJson<ArtifactDetail>(
    `/api/artifacts/${encodeURIComponent(cls)}/${encodeURIComponent(slug)}`,
  );
}

export function getPipeline(): Promise<PipelineData> {
  return getJson<PipelineData>('/api/pipeline');
}

// --- framework & scripts (FR4, FR8) ----------------------------------------

export function getFramework(): Promise<FrameworkData> {
  return getJson<FrameworkData>('/api/framework');
}

export function getScripts(): Promise<ScriptsResponse> {
  return getJson<ScriptsResponse>('/api/scripts');
}

/** POST an allow-listed read-only command; throws ApiError (400) when refused. */
export async function runScript(command: string, args: string[]): Promise<ExecResult> {
  const res = await fetch('/api/scripts/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command, args }),
  });
  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body && typeof body.error === 'string') message = body.error;
    } catch {
      // non-JSON error body — keep the status-derived message
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as ExecResult;
}

// --- registry & taxonomy editing (FR3) -------------------------------------

/** PUT a raw-markdown body; throws ApiError (e.g. 422 shape mismatch) on failure. */
async function putRaw(url: string, raw: string): Promise<void> {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw }),
  });
  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body && typeof body.error === 'string') message = body.error;
    } catch {
      // non-JSON error body — keep the status-derived message
    }
    throw new ApiError(res.status, message);
  }
}

export function listRegistries(): Promise<{ files: RegistryFile[] }> {
  return getJson<{ files: RegistryFile[] }>('/api/registry');
}

export function getRegistry(name: string): Promise<RegistryDetail> {
  return getJson<RegistryDetail>(`/api/registry/${encodeURIComponent(name)}`);
}

export function putRegistry(name: string, raw: string): Promise<void> {
  return putRaw(`/api/registry/${encodeURIComponent(name)}`, raw);
}

export function listTaxonomies(): Promise<{ files: TaxonomyFile[] }> {
  return getJson<{ files: TaxonomyFile[] }>('/api/taxonomy');
}

export function getTaxonomy(name: string): Promise<TaxonomyDetail> {
  return getJson<TaxonomyDetail>(`/api/taxonomy/${encodeURIComponent(name)}`);
}

export function putTaxonomy(name: string, raw: string): Promise<void> {
  return putRaw(`/api/taxonomy/${encodeURIComponent(name)}`, raw);
}

// --- memos (FR5) -----------------------------------------------------------

/** List memos, optionally filtered to executed / pending only. */
export function listMemos(executed?: boolean): Promise<MemoListResponse> {
  const suffix = executed === undefined ? '' : `?executed=${executed}`;
  return getJson<MemoListResponse>(`/api/memos${suffix}`);
}

export function getMemo(id: string): Promise<MemoDetail> {
  return getJson<MemoDetail>(`/api/memos/${encodeURIComponent(id)}`);
}

/** Toggle a memo's executed flag; throws ApiError on failure (404/400). */
export async function setMemoExecuted(id: string, executed: boolean): Promise<MemoDetail['memo']> {
  const res = await fetch(`/api/memos/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ executed }),
  });
  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body && typeof body.error === 'string') message = body.error;
    } catch {
      // non-JSON error body — keep the status-derived message
    }
    throw new ApiError(res.status, message);
  }
  const body = (await res.json()) as { memo: MemoDetail['memo'] };
  return body.memo;
}

// --- headless sessions (FR6) -----------------------------------------------

/** POST a generic JSON body; throws ApiError on non-2xx. */
async function postJson<T>(url: string, payload: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body && typeof body.error === 'string') message = body.error;
    } catch {
      // non-JSON error body — keep the status-derived message
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

/** Start a brainstorm session; returns the new session id (FR6.1). */
export function startSession(message: string, skill?: string): Promise<{ id: string }> {
  return postJson<{ id: string }>('/api/sessions', { message, skill });
}

/** Continue a session with a new turn — resumes the claude session (FR6.2). */
export function postMessage(id: string, message: string): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>(`/api/sessions/${encodeURIComponent(id)}/messages`, { message });
}

/** Abort (kill) a running session (NFR5). */
export function abortSession(id: string): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>(`/api/sessions/${encodeURIComponent(id)}/abort`, {});
}

/** List persisted sessions for the resume rail (FR6.3). */
export function listSessions(): Promise<SessionListResponse> {
  return getJson<SessionListResponse>('/api/sessions');
}

/** Fetch a session's meta + full transcript for reload (FR6.4). */
export function getSession(id: string): Promise<SessionDetail> {
  return getJson<SessionDetail>(`/api/sessions/${encodeURIComponent(id)}`);
}

/** The SSE URL for a session's event stream (used with native EventSource). */
export function sessionEventsUrl(id: string): string {
  return `/api/sessions/${encodeURIComponent(id)}/events`;
}

// --- creator end-to-end runs (FR7) -----------------------------------------

/** Start a creator run against a memo; returns the new run id (FR7.1). */
export function startCreatorRun(memoId: string): Promise<{ id: string }> {
  return postJson<{ id: string }>('/api/runs/creator', { memoId });
}

/** List persisted creator runs for the history rail (FR7.3). */
export function listRuns(): Promise<RunListResponse> {
  return getJson<RunListResponse>('/api/runs');
}

/** Fetch a run's meta + transcript + verification (FR7.2). */
export function getRun(id: string): Promise<RunDetail> {
  return getJson<RunDetail>(`/api/runs/${encodeURIComponent(id)}`);
}

/** Abort (kill) a running creator run (NFR5). */
export function abortRun(id: string): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>(`/api/runs/${encodeURIComponent(id)}/abort`, {});
}

/** The SSE URL for a run's event stream (used with native EventSource). */
export function runEventsUrl(id: string): string {
  return `/api/runs/${encodeURIComponent(id)}/events`;
}
