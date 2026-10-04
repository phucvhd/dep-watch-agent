// A thin, typed wrapper over the dep-watch API. Types come from the API's OpenAPI schema
// (`npm run gen:api` with the API running), so a change to `schemas.py` shows up here as a
// type error rather than a runtime surprise.
import type { components } from './schema'

type Schemas = components['schemas']
export type Health = Schemas['Health']
export type Dependency = Schemas['DependencyOut']
export type RepoFile = Schemas['RepoFile']
export type RepoScan = Schemas['RepoScanResponse']
export type DetectedDependency = Schemas['DetectedDependencyOut']
export type KafkaVersion = Schemas['KafkaVersion']
export type IssuePage = Schemas['IssuePage']
export type IssueSummary = Schemas['IssueSummary']
export type IssueDetail = Schemas['IssueDetail']
export type CheckRequest = Schemas['CheckRequest']
export type CheckResponse = Schemas['CheckResponse']
export type ScanRequest = Schemas['ScanRequest']
export type ScanResponse = Schemas['ScanResponse']
export type ScanItem = Schemas['ScanItemOut']
export type Evidence = Schemas['EvidenceOut']
export type DroppedEvidence = Schemas['DroppedEvidenceOut']
export type Job = Schemas['JobOut']
export type SyncState = Schemas['SyncState']
export type DatasetSummary = Schemas['DatasetSummary']
export type EvalRunSummary = Schemas['EvalRunSummary']
export type EvalRunRequest = Schemas['EvalRunRequest']
export type Answer = CheckResponse['answer']

const BASE = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(BASE + path, {
      ...init,
      headers: { 'content-type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(0, 'The API is not reachable. Start it with `uv run dep-watch-agent`.')
  }
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  return (await response.json()) as T
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      // FastAPI validation errors: [{loc: [..., field], msg}]
      return body.detail
        .map((e: { loc?: unknown[]; msg?: string }) => `${e.loc?.at(-1) ?? 'request'}: ${e.msg}`)
        .join('; ')
    }
  } catch {
    // not JSON
  }
  return `The API answered ${response.status} ${response.statusText}.`
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

function query(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  health: () => request<Health>('/health'),
  dependencies: () => request<Dependency[]>('/dependencies'),
  scanRepo: (files: RepoFile[]) => post<RepoScan>('/repo/scan', { files }),
  systems: () => request<string[]>('/systems'),
  versions: (project: string) => request<KafkaVersion[]>(`/versions${query({ project })}`),
  issues: (params: {
    project: string
    q?: string
    status?: string
    resolution?: string
    issue_type?: string
    fix_version?: string
    limit?: number
    offset?: number
  }) => request<IssuePage>(`/issues${query(params)}`),
  issue: (key: string) => request<IssueDetail>(`/issues/${encodeURIComponent(key)}`),
  check: (body: CheckRequest) => post<CheckResponse>('/check', body),
  startScan: (body: ScanRequest) => post<Job>('/scan', body),
  jobs: (kind?: string) => request<Job[]>(`/jobs${query({ kind })}`),
  job: (id: string) => request<Job>(`/jobs/${id}`),
  syncState: () => request<SyncState[]>('/sync/state'),
  startSync: (project: string) => post<Job>('/sync/jira', { project }),
  datasets: () => request<DatasetSummary[]>('/eval/datasets'),
  runs: () => request<EvalRunSummary[]>('/eval/runs'),
  startRun: (body: EvalRunRequest) => post<Job>('/eval/runs', body),
}
