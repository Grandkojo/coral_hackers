export interface TriggerRequest {
  source: string
  incident_id?: string
  query: string
  context: Record<string, string>
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
}

export type Phase = 'idle' | 'investigating' | 'complete'
