import { useState } from 'react'
import type { Phase, TriggerRequest, InvestigationState, ReportResponse } from './types/index'
import Header from './components/Header'
import InvestigationForm from './components/InvestigationForm'
import InvestigationPanel from './components/InvestigationPanel'
import ReportPanel from './components/ReportPanel'
import SourceBadges from './components/SourceBadges'
import { MOCK_REPORT_BASE } from './data/mockInvestigation'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [investigationState, setInvestigationState] = useState<InvestigationState | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Starts an investigation from the submitted trigger request; simulates orchestration iterations until real API is wired
  function handleSubmit(req: TriggerRequest) {
    const id = req.incident_id ?? `inv_${Math.random().toString(36).slice(2, 10)}`

    setIsSubmitting(true)
    setPhase('investigating')
    setInvestigationState({
      investigation_id: id,
      iteration_count: 1,
      evidence_rows: [],
      hypotheses: [`Analyzing: "${req.query}" — querying ${req.source} sources...`],
      confidence_score: 0.1,
      root_cause: null,
    })
    setIsSubmitting(false)

    // Simulate iteration 2: evidence collected, hypotheses narrowed
    setTimeout(() => {
      setInvestigationState((prev) =>
        prev
          ? {
              ...prev,
              iteration_count: 2,
              evidence_rows: [
                { source: 'github', type: 'pull_request', id: 'PR#234' },
                { source: 'sentry', type: 'fatal_error',  id: 'SENTRY-4521' },
                { source: 'vercel', type: 'deployment',   id: 'dpl_9e2xk'  },
              ],
              hypotheses: [
                'Auth service regression in PR #234 — token validation logic changed',
                'Database connection pool exhausted following deploy dpl_9e2xk',
              ],
              confidence_score: 0.67,
            }
          : prev,
      )
    }, 2200)

    // Simulate judge declaring sufficient confidence and emitting final report
    setTimeout(() => {
      setReport({ ...MOCK_REPORT_BASE, investigation_id: id })
      setPhase('complete')
    }, 4800)
  }

  // Resets the app to idle so the user can start a new investigation
  function handleReset() {
    setPhase('idle')
    setInvestigationState(null)
    setReport(null)
  }

  return (
    <div className="flex min-h-screen flex-col grid-bg">
      <Header phase={phase} />

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-10">
        {phase === 'idle' ? (
          <div className="space-y-8 fade-in">
            <div className="text-center space-y-5">
              <div className="pixel-card-accent inline-block px-8 py-5">
                <h1
                  className="font-pixel text-[var(--color-accent)]"
                  style={{ fontSize: '1rem', lineHeight: 2 }}
                >
                  INVINCIBLE
                </h1>
                <p className="font-mono text-[0.6rem] text-[var(--color-muted)] mt-1 tracking-widest">
                  PRODUCTION INCIDENT INTELLIGENCE
                </p>
              </div>
              <p className="font-display text-sm text-[var(--color-muted)] tracking-wide max-w-md mx-auto">
                Cross-source incident investigation. One query. One report.
              </p>
              <SourceBadges />
            </div>

            <InvestigationForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />

            <div className="pixel-card">
              <div className="border-b-2 border-[var(--color-edge)] px-5 py-2.5">
                <span className="section-label">EXAMPLE CORAL QUERY</span>
              </div>
              <div className="p-5">
                <pre className="font-mono text-[0.65rem] text-[var(--color-muted)] leading-loose overflow-x-auto">
                  {`SELECT g.title, s.error_message, sl.text\nFROM   github.pull_requests g\nJOIN   sentry.issues s\n         ON s.first_seen >= g.merged_at\nJOIN   slack.messages sl\n         ON sl.channel = '#incidents'\nWHERE  s.level = 'fatal'\nORDER  BY s.first_seen DESC;`}
                </pre>
              </div>
            </div>
          </div>
        ) : phase === 'investigating' && investigationState !== null ? (
          <InvestigationPanel state={investigationState} />
        ) : report !== null ? (
          <ReportPanel report={report} onReset={handleReset} />
        ) : null}
      </main>

      <footer className="border-t-2 border-[var(--color-edge)] px-6 py-3 text-center">
        <span className="font-mono text-[0.55rem] text-[var(--color-muted)]">
          INVINCIBLE v0.1.0-alpha · Pirates of the Coral-bean · WeMakeDevs Coral Hackathon 2026
        </span>
      </footer>
    </div>
  )
}
