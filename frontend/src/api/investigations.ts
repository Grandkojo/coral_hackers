import type {
  InvestigationListResponse,
  InvestigationSummary,
  QueryRunListResponse,
  QueryRunResponse,
  ReportResponse,
} from '../types/index'

import { apiFetch, readApiError } from './http'

export async function fetchInvestigations(limit = 50): Promise<InvestigationListResponse> {
  const response = await apiFetch(`/api/v1/investigations?limit=${limit}`)

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<InvestigationListResponse>
}

export async function fetchQueryRuns(investigationId: string): Promise<QueryRunListResponse> {
  const response = await apiFetch(`/api/v1/investigations/${investigationId}/query-runs`)

  if (!response.ok) {
    throw new Error(await readApiError(response))
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
  const response = await apiFetch(`/api/v1/investigations/${investigationId}/approve`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<ApproveResponse>
}

export async function deleteInvestigation(investigationId: string): Promise<void> {
  const response = await apiFetch(`/api/v1/investigations/${investigationId}`, {
    method: 'DELETE',
  })

  if (!response.ok && response.status !== 204) {
    throw new Error(await readApiError(response))
  }
}

export async function fetchReport(investigationId: string): Promise<ReportResponse> {
  const response = await apiFetch(`/api/v1/investigations/${investigationId}/report`)

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<ReportResponse>
}

export type { QueryRunResponse, InvestigationSummary }
