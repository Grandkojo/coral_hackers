import { useState } from 'react'
import type { ReportResponse } from '../types/index'
import { approveRemediation } from '../api/investigations'
import PixelCard from './PixelCard'
import QueryEvidencePanel from './QueryEvidencePanel'
import SeverityBar from './SeverityBar'
import StatusBadge from './StatusBadge'
import type { BadgeVariant } from './StatusBadge'

interface ReportPanelProps {
  report: ReportResponse
  onReset: () => void
}

function remediationBadge(mode: string): { variant: BadgeVariant, label: string } {
  return mode === 'autonomous_fix'
    ? { variant: 'autonomous', label: 'Autonomous fix' }
    : { variant: 'human-paired', label: 'Human approval req' }
}

export default function ReportPanel({ report, onReset }: ReportPanelProps) {
  const badge = remediationBadge(report.remediation_mode)
  const [approved, setApproved] = useState(false)
  const [approving, setApproving] = useState(false)
  const [approveError, setApproveError] = useState<string | null>(null)

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

  return (
    <div className="space-y-5 fade-up">
      <PixelCard
        title="Incident Report"
        titleRight={<StatusBadge label={badge.label} variant={badge.variant} />}
      >
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className="label shrink-0">Session</span>
          <span className="data-val font-mono text-[0.68rem] break-all">{report.investigation_id}</span>
        </div>

        <div className="mb-6">
          <SeverityBar score={report.severity_score} />
        </div>

        {report.root_cause ? (
          <div
            className="p-4 mb-6"
            style={{
              border: '1px solid var(--border)',
              background: 'var(--surface-2)',
            }}
          >
            <span className="label block mb-2" style={{ color: 'var(--green)' }}>
              Root cause
            </span>
            <p className="font-mono text-[0.68rem] leading-relaxed" style={{ color: 'var(--ink-2)' }}>
              {report.root_cause}
            </p>
          </div>
        ) : null}

        <hr className="divider mb-6" />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-6">
          <div>
            <span
              className="label block mb-3"
              style={{ color: 'var(--blue)' }}
            >
              Timeline
            </span>
            <ul className="space-y-2.5">
              {report.timeline.map((entry, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.64rem] leading-relaxed"
                  style={{ animation: `slide-in-row 280ms ${i * 60}ms ease-out both` }}
                >
                  <span style={{ color: 'var(--blue)', flexShrink: 0 }}>›</span>
                  <span style={{ color: 'var(--ink-2)' }}>{entry}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <span
              className="label block mb-3"
              style={{ color: 'var(--red)' }}
            >
              Suspects
            </span>
            <ul className="space-y-2.5">
              {report.suspects.map((s, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.64rem] leading-relaxed"
                  style={{ animation: `slide-in-row 280ms ${i * 60 + 40}ms ease-out both` }}
                >
                  <span style={{ color: 'var(--red)', flexShrink: 0 }}>!</span>
                  <span style={{ color: 'var(--ink-2)' }}>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <span
              className="label block mb-3"
              style={{ color: 'var(--accent)' }}
            >
              Citations
            </span>
            <ul className="space-y-2.5">
              {report.citations.map((c, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.64rem] leading-relaxed"
                  style={{ animation: `slide-in-row 280ms ${i * 60 + 80}ms ease-out both` }}
                >
                  <span style={{ color: 'var(--accent)', flexShrink: 0 }}>#</span>
                  <span style={{ color: 'var(--accent)' }}>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {report.unresolved_gaps.length > 0 ? (
          <div
            className="p-4 mb-6 space-y-2"
            style={{
              border: '1px solid var(--amber-dim)',
              background: 'var(--amber-dim)',
              borderColor: 'var(--amber)',
            }}
          >
            <span className="label block" style={{ color: 'var(--amber)' }}>
              Unresolved gaps
            </span>
            {report.unresolved_gaps.map((gap, i) => (
              <p key={i} className="font-mono text-[0.64rem]" style={{ color: 'var(--amber)' }}>
                — {gap}
              </p>
            ))}
          </div>
        ) : null}

        <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center sm:justify-between gap-3 pt-1">
          <button className="btn btn-ghost justify-center sm:justify-start" onClick={onReset}>
            New investigation
          </button>

          {report.remediation_mode === 'autonomous_fix' ? (
            <button className="btn btn-primary justify-center" disabled>
              Autonomous fix eligible
            </button>
          ) : approved ? (
            <button className="btn btn-primary justify-center" disabled>
              Remediation approved
            </button>
          ) : (
            <button
              className="btn btn-primary justify-center"
              onClick={() => void handleApprove()}
              disabled={approving}
            >
              {approving ? 'Approving…' : 'Approve remediation'}
            </button>
          )}
        </div>

        {approveError ? (
          <p className="font-mono text-[0.62rem] mt-3" style={{ color: 'var(--red)' }}>
            {approveError}
          </p>
        ) : null}
      </PixelCard>

      <QueryEvidencePanel investigationId={report.investigation_id} />
    </div>
  )
}
