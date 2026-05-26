import type { ReportResponse } from '../types/index'
import PixelCard from './PixelCard'
import SeverityBar from './SeverityBar'
import StatusBadge from './StatusBadge'
import type { BadgeVariant } from './StatusBadge'

interface ReportPanelProps {
  report: ReportResponse
  onReset: () => void
}

function getRemediationVariant(mode: string): BadgeVariant {
  return mode === 'autonomous_fix' ? 'autonomous' : 'human-paired'
}

function getRemediationLabel(mode: string): string {
  return mode === 'autonomous_fix' ? 'AUTONOMOUS FIX' : 'HUMAN APPROVAL REQ'
}

export default function ReportPanel({ report, onReset }: ReportPanelProps) {
  const remediationVariant = getRemediationVariant(report.remediation_mode)
  const remediationLabel = getRemediationLabel(report.remediation_mode)

  return (
    <div className="space-y-4 fade-in">
      <PixelCard
        title="INCIDENT REPORT"
        titleRight={<StatusBadge label={remediationLabel} variant={remediationVariant} />}
      >
        {/* ID + severity */}
        <div className="mb-1 flex items-center gap-2">
          <span className="section-label">SESSION ID</span>
          <span className="data-val text-[0.7rem]">{report.investigation_id}</span>
        </div>
        <div className="mb-5">
          <SeverityBar score={report.severity_score} />
        </div>

        <hr className="pixel-hr mb-5" />

        {/* Three-column data grid */}
        <div className="grid gap-5 md:grid-cols-3 mb-5">
          {/* Timeline */}
          <div>
            <div className="section-label mb-2.5 text-[var(--color-cyan)]">TIMELINE</div>
            <ul className="space-y-2">
              {report.timeline.map((entry, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.62rem] text-[var(--color-ink)] leading-relaxed"
                >
                  <span className="text-[var(--color-cyan)] flex-shrink-0">›</span>
                  <span>{entry}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Suspects */}
          <div>
            <div className="section-label mb-2.5 text-[var(--color-danger)]">SUSPECTS</div>
            <ul className="space-y-2">
              {report.suspects.map((s, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.62rem] text-[var(--color-ink)] leading-relaxed"
                >
                  <span className="text-[var(--color-danger)] flex-shrink-0">!</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Citations */}
          <div>
            <div className="section-label mb-2.5 text-[var(--color-accent)]">CITATIONS</div>
            <ul className="space-y-2">
              {report.citations.map((c, i) => (
                <li
                  key={i}
                  className="flex gap-2 font-mono text-[0.62rem] leading-relaxed"
                >
                  <span className="text-[var(--color-accent)] flex-shrink-0">#</span>
                  <span className="text-[var(--color-accent)]">{c}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Unresolved gaps */}
        {report.unresolved_gaps.length > 0 ? (
          <div
            className="border-2 p-3 mb-5 space-y-1"
            style={{
              borderColor: 'var(--color-warning)',
              background: 'rgba(255,170,0,0.04)',
            }}
          >
            <div className="section-label mb-1.5" style={{ color: 'var(--color-warning)' }}>
              UNRESOLVED GAPS
            </div>
            {report.unresolved_gaps.map((gap, i) => (
              <p key={i} className="font-mono text-[0.62rem]" style={{ color: 'var(--color-warning)' }}>
                ⚠ {gap}
              </p>
            ))}
          </div>
        ) : null}

        {/* Actions */}
        <div className="flex flex-wrap items-center justify-end gap-3 pt-1">
          <button className="pixel-btn-ghost" onClick={onReset}>
            + NEW INVESTIGATION
          </button>
          {report.remediation_mode === 'autonomous_fix' ? (
            <button className="pixel-btn">APPLY AUTONOMOUS FIX</button>
          ) : (
            <button className="pixel-btn" disabled>
              AWAITING HUMAN APPROVAL
            </button>
          )}
        </div>
      </PixelCard>
    </div>
  )
}
