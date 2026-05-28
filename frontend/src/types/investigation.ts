export interface InvestigationState {
  investigation_id: string
  iteration_count: number
  evidence_rows: Record<string, unknown>[]
  hypotheses: string[]
  confidence_score: number
  root_cause: string | null
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

export type InvestigationStatus = 'idle' | 'investigating' | 'complete' | 'error'
