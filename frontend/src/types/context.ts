import type { DashboardTriggerRequest } from './api'

export interface InvestigationContextValue {
  investigationState: any | null
  report: any | null
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

export interface AuthContextValue {
  user: any | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<import('./auth').User>
  signup: (email: string, password: string, orgName: string) => Promise<import('./auth').User>
  logout: () => void
  clearError: () => void
}

export interface OrgContextValue {
  orgId: string | null
  orgName: string | null
  setOrg: (orgId: string, orgName: string) => void
  clearOrg: () => void
}
