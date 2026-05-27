export interface TriggerRequest {
  source: string
  incident_id?: string
  query: string
  vercel_url?: string
  context: Record<string, string>
}

export interface DashboardTriggerRequest {
  query?: string
  incident_id?: string
  vercel_url?: string
  context?: Record<string, string>
}

export interface InvestigationState {
  investigation_id: string
  iteration_count: number
  evidence_rows: Record<string, unknown>[]
  hypotheses: string[]
  confidence_score: number
  root_cause: string | null
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

export interface InvestigationSummary {
  investigation_id: string
  status: string
  source: string
  user_query: string
  iteration_count: number
  confidence_score: number
  root_cause: string | null
  severity_score: number | null
  remediation_mode: string | null
  approved_at: string | null
  created_at: string | null
  completed_at: string | null
}

export interface InvestigationListResponse {
  investigations: InvestigationSummary[]
  total: number
}

export type Phase = 'idle' | 'investigating' | 'complete'
