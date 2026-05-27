import type { DashboardTriggerRequest, ReportResponse } from '../types/index'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function triggerDashboardInvestigation(
  payload: DashboardTriggerRequest,
): Promise<ReportResponse> {
  const response = await fetch(`${API_BASE}/api/v1/triggers/dashboard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Investigation failed (${response.status})`)
  }

  return response.json() as Promise<ReportResponse>
}
