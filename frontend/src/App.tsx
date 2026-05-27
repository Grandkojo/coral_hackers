import { useState } from 'react'
import type { DashboardTriggerRequest, InvestigationState, ReportResponse } from './types/index'
import Header from './layout/Header'
import Footer from './layout/Footer'
import InvestigationForm from './components/InvestigationForm'
import InvestigationPanel from './components/InvestigationPanel'
import InvestigationHistory from './components/InvestigationHistory'
import ReportPanel from './components/ReportPanel'
import HeroSection from './components/HeroSection'
import ExampleQueryCard from './components/ExampleQueryCard'
import AmbientBackdrop from './components/AmbientBackdrop'
import { fetchReport } from './api/investigations'
import { triggerDashboardInvestigation } from './api/triggers'

type AppView = 'home' | 'investigating' | 'report'

export default function App() {
  const [view, setView] = useState<AppView>('home')
  const [investigationState, setInvestigationState] = useState<InvestigationState | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [selectedInvestigationId, setSelectedInvestigationId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoadingReport, setIsLoadingReport] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0)

  async function handleSubmit(req: DashboardTriggerRequest) {
    setError(null)
    setIsSubmitting(true)
    setView('investigating')
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
      setView('report')
      setHistoryRefreshKey((key) => key + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Investigation failed')
      setView('home')
      setInvestigationState(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSelectHistory(investigationId: string) {
    setError(null)
    setIsLoadingReport(true)
    setSelectedInvestigationId(investigationId)

    try {
      const loaded = await fetchReport(investigationId)
      setReport(loaded)
      setView('report')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investigation')
      setView('home')
      setReport(null)
      setSelectedInvestigationId(null)
    } finally {
      setIsLoadingReport(false)
    }
  }

  function handleReset() {
    setView('home')
    setInvestigationState(null)
    setReport(null)
    setSelectedInvestigationId(null)
    setError(null)
  }

  return (
    <div className="app-shell">
      <AmbientBackdrop />
      <Header
        onHome={view !== 'home' ? handleReset : undefined}
        showHistoryNav={view === 'report'}
      />

      <main className="app-main">
        <div className="app-container">
          {view === 'home' ? (
            <div className="landing-layout fade-up">
              <HeroSection
                alerts={
                  <>
                    {error ? (
                      <div className="alert-banner" role="alert">
                        {error}
                      </div>
                    ) : null}
                    {isLoadingReport ? (
                      <div className="alert-banner">Loading investigation report…</div>
                    ) : null}
                  </>
                }
                form={
                  <InvestigationForm
                    variant="hero"
                    onSubmit={handleSubmit}
                    isSubmitting={isSubmitting}
                  />
                }
              />

              <InvestigationHistory
                onSelect={(id) => void handleSelectHistory(id)}
                selectedId={selectedInvestigationId}
                refreshKey={historyRefreshKey}
              />

              <ExampleQueryCard />
            </div>
          ) : view === 'investigating' && investigationState !== null ? (
            <InvestigationPanel state={investigationState} />
          ) : report !== null ? (
            <div className="report-layout fade-up">
              <aside className="report-sidebar">
                <InvestigationHistory
                  compact
                  onSelect={(id) => void handleSelectHistory(id)}
                  selectedId={selectedInvestigationId}
                  refreshKey={historyRefreshKey}
                />
              </aside>
              <div className="report-main">
                <ReportPanel report={report} onReset={handleReset} />
              </div>
            </div>
          ) : null}
        </div>
      </main>

      <Footer />
    </div>
  )
}
