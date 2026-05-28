import { createContext } from 'react'
import type { DashboardTriggerRequest, ReportResponse } from '../types/api'
import type { InvestigationState } from '../types/investigation'

export interface InvestigationContextValue {
  investigationState: InvestigationState | null
  report: ReportResponse | null
  selectedInvestigationId: string | null
  isSubmitting: boolean
  isLoadingReport: boolean
  error: string | null
  historyRefreshKey: number
  handleSubmit: (req: DashboardTriggerRequest) => Promise<string>
  handleSelectHistory: (investigationId: string) => Promise<void>
  handleReset: () => void
  setError: (error: string | null) => void
}

export const InvestigationContext = createContext<InvestigationContextValue | null>(null)
