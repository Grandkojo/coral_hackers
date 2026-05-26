import type { ReportResponse } from '../types/index'
import PixelCard from './PixelCard'
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

// Final report view — maps to ReportResponse backend schema
export default function ReportPanel({ report, onReset }: ReportPanelProps) {
  const badge = remediationBadge(report.remediation_mode)

  return (
    <div className="space-y-5 fade-up">
      <PixelCard
        title="Incident Report"
        titleRight={<StatusBadge label={badge.label} variant={badge.variant} />}
      >
        {/* Session ID */}
        <div className="flex items-center gap-2 mb-4">
          <span className="label">Session</span>
          <span className="data-val font-mono text-[0.68rem]">{report.investigation_id}</span>
        </div>

        {/* Severity */}
        <div className="mb-6">
          <SeverityBar score={report.severity_score} />
        </div>

        <hr className="divider mb-6" />

        {/* Three-column evidence grid */}
        <div className="grid gap-6 md:grid-cols-3 mb-6">
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

        {/* Unresolved gaps */}
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

        {/* Action row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <button className="btn btn-ghost" onClick={onReset}>
            New investigation
          </button>
          {report.remediation_mode === 'autonomous_fix' ? (
            <button className="btn btn-primary">Apply autonomous fix</button>
          ) : (
            <button className="btn btn-primary" disabled>
              Awaiting human approval
            </button>
          )}
        </div>
      </PixelCard>
    </div>
  )
}
