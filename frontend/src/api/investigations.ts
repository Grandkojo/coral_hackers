import type {
  InvestigationListResponse,
  InvestigationSummary,
  QueryRunListResponse,
  QueryRunResponse,
  ReportResponse,
} from '../types/index'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function fetchInvestigations(limit = 50): Promise<InvestigationListResponse> {
  const response = await fetch(`${API_BASE}/api/v1/investigations?limit=${limit}`)

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to load investigations (${response.status})`)
  }

  return response.json() as Promise<InvestigationListResponse>
}

export async function fetchQueryRuns(investigationId: string): Promise<QueryRunListResponse> {
  const response = await fetch(`${API_BASE}/api/v1/investigations/${investigationId}/query-runs`)

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to load query runs (${response.status})`)
  }

  return response.json() as Promise<QueryRunListResponse>
}

export interface ApproveResponse {
  investigation_id: string
  approved: boolean
  approved_at: string | null
  message: string
}

export async function approveRemediation(investigationId: string): Promise<ApproveResponse> {
  const response = await fetch(`${API_BASE}/api/v1/investigations/${investigationId}/approve`, {
    method: 'POST',
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Approval failed (${response.status})`)
  }

  return response.json() as Promise<ApproveResponse>
}

export async function fetchReport(investigationId: string): Promise<ReportResponse> {
  const response = await fetch(`${API_BASE}/api/v1/investigations/${investigationId}/report`)

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Failed to load report (${response.status})`)
  }

  return response.json() as Promise<ReportResponse>
}

export type { QueryRunResponse, InvestigationSummary }
