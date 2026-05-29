import { useCallback, useState } from 'react'
import type { ReportResponse } from '../types/index'
import { approveRemediation } from '../api/investigations'
import { dedupeStrings, parseCitationRunId } from '../lib/reportFormat'
import PixelCard from './PixelCard'
import QueryEvidencePanel from './QueryEvidencePanel'
import ReportTimeline from './ReportTimeline'
import GithubBudgetHint from './GithubBudgetHint'
import SeverityBar from './SeverityBar'
import StatusBadge from './StatusBadge'
import type { BadgeVariant } from './StatusBadge'

interface ReportPanelProps {
  report: ReportResponse
  onReset: () => void
}

function remediationBadge(mode: string): { variant: BadgeVariant; label: string } {
  return mode === 'autonomous_fix'
    ? { variant: 'autonomous', label: 'Autonomous fix' }
    : { variant: 'human-paired', label: 'Human approval required' }
}

export default function ReportPanel({ report, onReset }: ReportPanelProps) {
  const badge = remediationBadge(report.remediation_mode)
  const suspects = dedupeStrings(report.suspects)
  const [approved, setApproved] = useState(false)
  const [approving, setApproving] = useState(false)
  const [approveError, setApproveError] = useState<string | null>(null)
  const [highlightRunId, setHighlightRunId] = useState<number | null>(null)

  const scrollToQueryRun = useCallback((runId: number) => {
    setHighlightRunId(runId)
    const el = document.getElementById(`query-run-${runId}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.setTimeout(() => setHighlightRunId(null), 2400)
  }, [])

  async function handleApprove() {
    setApproveError(null)
    setApproving(true)
    try {
      await approveRemediation(report.investigation_id)
      setApproved(true)
    } catch (err) {
      setApproveError(err instanceof Error ? err.message : 'Approval failed')
    } finally {
      setApproving(false)
    }
  }

  const iterationCount = report.timeline.filter((e) =>
    /^Iteration\s+\d+/i.test(e),
  ).length

  return (
    <div className="report-panel fade-up">
      <div className="report-summary-grid">
        <PixelCard
          className="report-summary-card"
          title="Incident Report"
          titleRight={<StatusBadge label={badge.label} variant={badge.variant} />}
        >
          <div className="report-meta-row">
            <span className="label">Session</span>
            <code className="report-session-id">{report.investigation_id}</code>
          </div>
          <SeverityBar score={report.severity_score} />
          <GithubBudgetHint
            used={report.github_queries_executed ?? 0}
            max={report.github_queries_max ?? 2}
            rateLimited={report.github_rate_limited ?? false}
            variant="report"
          />
        </PixelCard>

        <div className="report-stats">
          <div className="report-stat">
            <span className="report-stat-value">{iterationCount}</span>
            <span className="report-stat-label">Iterations</span>
          </div>
          <div className="report-stat">
            <span className="report-stat-value">{suspects.length}</span>
            <span className="report-stat-label">Suspects</span>
          </div>
          <div className="report-stat">
            <span className="report-stat-value">{report.citations.length}</span>
            <span className="report-stat-label">Citations</span>
          </div>
          <div className="report-stat">
            <span className="report-stat-value">{report.unresolved_gaps.length}</span>
            <span className="report-stat-label">Gaps</span>
          </div>
          <div
            className={`report-stat report-stat-github${
              report.github_rate_limited ? ' report-stat-github--limited' : ''
            }`}
          >
            <span className="report-stat-value">
              {report.github_queries_executed ?? 0}/{report.github_queries_max ?? 2}
            </span>
            <span className="report-stat-label">GitHub queries</span>
          </div>
        </div>
      </div>

      {report.root_cause ? (
        <div className="report-root-cause">
          <span className="label report-section-label">Root cause</span>
          <p className="report-root-cause-text">{report.root_cause}</p>
        </div>
      ) : (
        <div className="report-root-cause report-root-cause-missing">
          <span className="label report-section-label">Root cause</span>
          <p className="report-root-cause-text">
            Not finalized — review evidence below and unresolved gaps.
          </p>
        </div>
      )}

      <div className="report-sections">
        <section className="report-section">
          <div className="report-section-head">
            <h2 className="report-section-title">Investigation steps</h2>
            <span className="report-section-hint">Expand each step for full planner rationale</span>
          </div>
          <ReportTimeline entries={report.timeline} />
        </section>

        <section className="report-section">
          <div className="report-section-head">
            <h2 className="report-section-title">Leading suspects</h2>
            <span className="report-section-hint">Deduplicated hypotheses from Coral evidence</span>
          </div>
          {suspects.length === 0 ? (
            <p className="report-empty">No suspects identified from query results.</p>
          ) : (
            <ul className="report-suspects-list">
              {suspects.map((suspect, i) => (
                <li key={i} className="report-suspect-card">
                  <span className="report-suspect-index">{i + 1}</span>
                  <p className="report-suspect-text">{suspect}</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        {report.citations.length > 0 ? (
          <section className="report-section">
            <div className="report-section-head">
              <h2 className="report-section-title">Evidence citations</h2>
              <span className="report-section-hint">Jump to matching query below</span>
            </div>
            <div className="report-citation-chips">
              {report.citations.map((citation, i) => {
                const runId = parseCitationRunId(citation)
                return (
                  <button
                    key={i}
                    type="button"
                    className="report-citation-chip"
                    disabled={runId === null}
                    onClick={() => runId !== null && scrollToQueryRun(runId)}
                    title={runId !== null ? 'View query evidence' : citation}
                  >
                    {runId !== null ? `Query #${runId}` : citation}
                  </button>
                )
              })}
            </div>
          </section>
        ) : null}
      </div>

      {report.unresolved_gaps.length > 0 ? (
        <div className="report-gaps" role="alert">
          <span className="label report-section-label">Unresolved gaps</span>
          <ul className="report-gaps-list">
            {report.unresolved_gaps.map((gap, i) => (
              <li key={i}>{gap}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="report-actions">
        <button type="button" className="btn btn-ghost" onClick={onReset}>
          New investigation
        </button>

        {report.remediation_mode === 'autonomous_fix' ? (
          <button type="button" className="btn btn-primary" disabled>
            Autonomous fix eligible
          </button>
        ) : approved ? (
          <button type="button" className="btn btn-primary" disabled>
            Remediation approved
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void handleApprove()}
            disabled={approving}
          >
            {approving ? 'Approving…' : 'Approve remediation'}
          </button>
        )}
      </div>

      {approveError ? (
        <p className="report-error">{approveError}</p>
      ) : null}

      <QueryEvidencePanel
        investigationId={report.investigation_id}
        highlightRunId={highlightRunId}
      />
    </div>
  )
}
