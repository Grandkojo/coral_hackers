import { useState } from 'react'
import type { Phase, TriggerRequest, InvestigationState, ReportResponse } from './types/index'
import Header from './layout/Header'
import Footer from './layout/Footer'
import InvestigationForm from './components/InvestigationForm'
import InvestigationPanel from './components/InvestigationPanel'
import ReportPanel from './components/ReportPanel'
import SourceBadges from './components/SourceBadges'
import ASCIIText from './components/ASCIIText'
import { MOCK_REPORT_BASE } from './data/mockInvestigation'
import { useHeroFontSize } from './hooks/useFontSize'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [investigationState, setInvestigationState] = useState<InvestigationState | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const heroFontSize = useHeroFontSize()

  // Starts an investigation from the submitted trigger; simulates orchestration iterations until real API is wired
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

    // Iteration 2 — evidence collected, hypotheses narrowed
    setTimeout(() => {
      setInvestigationState((prev) =>
        prev
          ? {
              ...prev,
              iteration_count: 2,
              evidence_rows: [
                { source: 'github', type: 'pull_request', id: 'PR#234' },
                { source: 'sentry', type: 'fatal_error', id: 'SENTRY-4521' },
                { source: 'vercel', type: 'deployment', id: 'dpl_9e2xk' },
              ],
              hypotheses: [
                'Auth service regression in PR #234 — token validation logic changed',
                'DB connection pool exhausted following deploy dpl_9e2xk',
              ],
              confidence_score: 0.67,
            }
          : prev,
      )
    }, 2200)

    // Judge declares sufficient confidence — emit final report
    setTimeout(() => {
      setReport({ ...MOCK_REPORT_BASE, investigation_id: id })
      setPhase('complete')
    }, 4800)
  }

  // Resets back to idle so the user can start a new investigation
  function handleReset() {
    setPhase('idle')
    setInvestigationState(null)
    setReport(null)
  }

  return (
    <div className="flex min-h-screen flex-col" style={{ background: 'var(--bg)' }}>
      <Header />

      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-5 pt-14 mb-14">
        {phase === 'idle' ? (
            <div className="fade-up flex flex-col gap-16">
              {/* Hero */}
              <section className="flex flex-col items-center text-center gap-6">
                <p
                  className="font-mono text-[0.6rem] tracking-widest"
                  style={{ color: 'var(--muted)' }}
                >
                  // production incident intelligence
                </p>

                <div
                  className="relative w-full"
                  style={{ height: heroFontSize < 150 ? '200px' : heroFontSize < 250 ? '260px' : '320px' }}
                >
                  <ASCIIText text="INVINCIBLE" enableWaves asciiFontSize={6} textFontSize={heroFontSize} planeBaseHeight={10} />
                </div>

                <p
                  className="font-body text-base max-w-sm leading-relaxed"
                  style={{ color: 'var(--ink-2)' }}
                >
                  Cross-source incident investigation.<br />One query. One report. Optionally, one fix.
                </p>

                <SourceBadges />
              </section>

              {/* Investigation form */}
              <InvestigationForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />

              {/* Example Coral query */}
              <div className="card">
                <div className="card-header">
                  <span className="label">Example Coral query</span>
                  <span className="font-mono text-[0.56rem]" style={{ color: 'var(--muted)' }}>
                    cross-source JOIN — no ETL
                  </span>
                </div>
                <div className="p-5">
                  <pre
                    className="font-mono text-[0.68rem] leading-loose overflow-x-auto"
                    style={{ color: 'var(--ink-2)' }}
                  >
                    {`SELECT  g.title, s.error_message, sl.text\nFROM    github.pull_requests g\nJOIN    sentry.issues s\n          ON s.first_seen >= g.merged_at\nJOIN    slack.messages sl\n          ON sl.channel = '#incidents'\nWHERE   s.level = 'fatal'\nORDER BY s.first_seen DESC;`}
                  </pre>
                </div>
              </div>
            </div>
          ) : phase === 'investigating' && investigationState !== null ? (
            <InvestigationPanel state={investigationState} />
          ) : report !== null ? (
            <ReportPanel report={report} onReset={handleReset} />
          ) : null}
        </div>
      </main>

      <Footer />
    </div>
  )
}
