import type { InvestigationState } from '../types/index'
import PixelCard from './PixelCard'

interface InvestigationPanelProps {
  state: InvestigationState
}

function getConfidenceMeta(score: number): { color: string, label: string } {
  if (score >= 0.7) return { color: 'var(--red)', label: 'High confidence' }
  if (score >= 0.4) return { color: 'var(--amber)', label: 'Building...' }
  return { color: 'var(--muted)', label: 'Collecting evidence' }
}

// Live view of the orchestration loop state — maps to InvestigationState backend schema
export default function InvestigationPanel({ state }: InvestigationPanelProps) {
  const pct = Math.round(state.confidence_score * 100)
  const meta = getConfidenceMeta(state.confidence_score)

  return (
    <div className="space-y-5 fade-up">
      <PixelCard variant="accent" title="Investigation running">
        {/* Scan animation bar */}
        <div className="relative h-px overflow-hidden" style={{ background: 'var(--accent-border)' }}>
          <div className="scan-line" />
        </div>

        {/* Metrics row */}
        <div className="grid grid-cols-3 gap-3 my-5">
          <div className="metric-box">
            <div className="label mb-2">Iteration</div>
            <div className="data-val text-xl sm:text-2xl font-bold">{state.iteration_count}</div>
          </div>
          <div className="metric-box">
            <div className="label mb-2">Evidence rows</div>
            <div className="data-val text-xl sm:text-2xl font-bold">{state.evidence_rows.length}</div>
          </div>
          <div className="metric-box">
            <div className="label mb-2">Confidence</div>
            <div
              className="font-mono text-xl sm:text-2xl font-bold"
              style={{ color: meta.color }}
            >
              {pct}%
            </div>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="space-y-1.5 mb-5">
          <div className="flex items-center justify-between">
            <span className="label">Confidence score</span>
            <span className="font-mono text-[0.6rem]" style={{ color: meta.color }}>
              {meta.label}
            </span>
          </div>
          <div className="severity-track">
            <div
              className="severity-fill"
              style={{ width: `${pct}%`, backgroundColor: meta.color }}
            />
          </div>
        </div>

        <hr className="divider mb-5" />

        {/* Hypotheses */}
        <div className="mb-5">
          <span className="label block mb-3">Active hypotheses</span>
          <ul className="space-y-3">
            {state.hypotheses.map((h, i) => (
              <li
                key={i}
                className="flex gap-3 font-mono text-[0.72rem] leading-relaxed"
                style={{ animation: `slide-in-row 300ms ${i * 80}ms ease-out both` }}
              >
                <span className="font-bold flex-shrink-0" style={{ color: 'var(--accent)' }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span style={{ color: 'var(--ink-2)' }}>{h}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Root cause */}
        <div
          className="p-4 space-y-1.5"
          style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)' }}
        >
          <span className="label block">Root cause</span>
          {state.root_cause ? (
            <p className="font-mono text-[0.72rem]" style={{ color: 'var(--accent)' }}>
              {state.root_cause}
            </p>
          ) : (
            <p className="font-mono text-[0.72rem]" style={{ color: 'var(--muted)' }}>
              analyzing<span className="blink">_</span>
            </p>
          )}
        </div>

        {/* Session footer */}
        <div className="mt-4 flex items-center gap-2" style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
          <span className="label">Session</span>
          <span className="data-val font-mono text-[0.68rem]">{state.investigation_id}</span>
        </div>
      </PixelCard>
    </div>
  )
}
