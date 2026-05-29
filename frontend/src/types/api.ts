export interface DashboardTriggerRequest {
  query?: string
  incident_id?: string
  vercel_url?: string
  context?: Record<string, string>
}

export interface TriggerRequest {
  source: string
  incident_id?: string
  query: string
  vercel_url?: string
  context: Record<string, string>
}

export interface ReportResponse {
  investigation_id: string
  timeline: string[]
  suspects: string[]
  citations: string[]
  unresolved_gaps: string[]
  severity_score: number
  remediation_mode: string
  root_cause: string | null
}

export interface QueryRunResponse {
  id: number
  investigation_id: string
  iteration: number
  sql: string
  rationale: string | null
  row_count: number
  rows: Record<string, unknown>[]
  citation: string
  ran_at: string | null
}

export interface QueryRunListResponse {
  investigation_id: string
  query_runs: QueryRunResponse[]
}

export interface ApiErrorResponse {
  statusCode: number
  message: string
  details?: Record<string, unknown>
  timestamp?: string
}
