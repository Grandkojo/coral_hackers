import type { DashboardTriggerRequest, ReportResponse } from '../types/index'

import { apiFetch, readApiError } from './http'

export async function triggerDashboardInvestigation(
  payload: DashboardTriggerRequest,
): Promise<ReportResponse> {
  const response = await apiFetch('/api/v1/triggers/dashboard', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await readApiError(response))
  }

  return response.json() as Promise<ReportResponse>
}
