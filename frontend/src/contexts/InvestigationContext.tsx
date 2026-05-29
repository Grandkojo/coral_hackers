import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { DashboardTriggerRequest, InvestigationState, ReportResponse } from '../types/index'
import { fetchReport } from '../api/investigations'
import { triggerDashboardInvestigation } from '../api/triggers'

interface InvestigationContextType {
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

const InvestigationContext = createContext<InvestigationContextType | undefined>(undefined)

export function InvestigationProvider({ children }: { children: ReactNode }) {
  const [investigationState, setInvestigationState] = useState<InvestigationState | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [selectedInvestigationId, setSelectedInvestigationId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingReport, setIsLoadingReport] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)

  const handleSubmit = useCallback(async (req: DashboardTriggerRequest) => {
    setError(null)
    setIsSubmitting(true)
    setSelectedInvestigationId(null)
    setInvestigationState({
      investigation_id: req.incident_id ?? 'pending',
      iteration_count: 0,
      evidence_rows: [],
      hypotheses: [
        req.query
          ? `Running Coral investigation: ${req.query}`
          : `Inspecting Vercel deployment ${req.vercel_url}`,
      ],
      confidence_score: 0.1,
      root_cause: null,
    })

    try {
      const result = await triggerDashboardInvestigation(req)
      setReport(result)
      setSelectedInvestigationId(result.investigation_id)
      setInvestigationState({
        investigation_id: result.investigation_id,
        iteration_count: result.citations.length,
        evidence_rows: result.suspects.map((s) => ({ summary: s })),
        hypotheses: result.suspects,
        confidence_score: result.severity_score,
        root_cause: result.root_cause,
      })
      setHistoryRefreshKey((key) => key + 1)
      return result.investigation_id
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Investigation failed'
      setError(errorMsg)
      setInvestigationState(null)
      throw err
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const handleSelectHistory = useCallback(async (investigationId: string) => {
    setError(null)
    setIsLoadingReport(true)
    setSelectedInvestigationId(investigationId)

    try {
      const loaded = await fetchReport(investigationId)
      setReport(loaded)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load investigation'
      setError(errorMsg)
      setReport(null)
      setSelectedInvestigationId(null)
      throw err
    } finally {
      setIsLoadingReport(false)
    }
  }, [])

  const handleReset = useCallback(() => {
    setInvestigationState(null)
    setReport(null)
    setSelectedInvestigationId(null)
    setError(null)
  }, [])

  return (
    <InvestigationContext.Provider
      value={{
        investigationState,
        report,
        selectedInvestigationId,
        isSubmitting,
        isLoadingReport,
        error,
        historyRefreshKey,
        handleSubmit,
        handleSelectHistory,
        handleReset,
        setError,
      }}
    >
      {children}
    </InvestigationContext.Provider>
  )
}

export function useInvestigation() {
  const context = useContext(InvestigationContext)
  if (context === undefined) {
    throw new Error('useInvestigation must be used within InvestigationProvider')
  }
  return context
}
