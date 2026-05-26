import type { InvestigationState } from '../types/index'
import PixelCard from './PixelCard'

interface InvestigationPanelProps {
  state: InvestigationState
}

function getConfidenceColor(score: number): string {
  if (score >= 0.7) return 'var(--color-danger)'
  if (score >= 0.4) return 'var(--color-warning)'
  return 'var(--color-accent)'
}

export default function InvestigationPanel({ state }: InvestigationPanelProps) {
  const pct = Math.round(state.confidence_score * 100)
  const barColor = getConfidenceColor(state.confidence_score)

  return (
    <div className="space-y-4 fade-in">
      <PixelCard variant="accent" title="INVESTIGATION IN PROGRESS">
        {/* Scan line effect */}
        <div className="relative h-0 overflow-visible">
          <div className="scan-anim" />
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-2 mb-5 text-center">
          <div className="pixel-card py-3 px-2">
            <div className="section-label mb-1.5">ITERATION</div>
            <div className="data-val text-3xl font-bold">{state.iteration_count}</div>
          </div>
          <div className="pixel-card py-3 px-2">
            <div className="section-label mb-1.5">EVIDENCE</div>
            <div className="data-val text-3xl font-bold">{state.evidence_rows.length}</div>
          </div>
          <div className="pixel-card py-3 px-2">
            <div className="section-label mb-1.5">CONFIDENCE</div>
            <div className="data-val text-3xl font-bold">{pct}%</div>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="mb-5 space-y-1.5">
          <div className="section-label">CONFIDENCE SCORE</div>
          <div className="severity-bar-track">
            <div
              className="severity-bar-fill"
              style={{ width: `${pct}%`, backgroundColor: barColor }}
            />
          </div>
        </div>

        <hr className="pixel-hr mb-5" />

        {/* Hypotheses */}
        <div className="mb-5">
          <div className="section-label mb-3">ACTIVE HYPOTHESES</div>
          <ul className="space-y-2.5">
            {state.hypotheses.map((h, i) => (
              <li
                key={i}
                className="flex gap-2.5 font-mono text-[0.7rem] leading-relaxed text-[var(--color-ink)]"
              >
                <span className="text-[var(--color-accent)] flex-shrink-0 font-bold">
                  [{i + 1}]
                </span>
                <span>{h}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Root cause */}
        <div className="pixel-card px-4 py-3">
          <div className="section-label mb-1.5">ROOT CAUSE</div>
          {state.root_cause ? (
            <span className="font-mono text-[0.72rem] text-[var(--color-accent)]">
              {state.root_cause}
            </span>
          ) : (
            <span className="font-mono text-[0.72rem] text-[var(--color-muted)]">
              analyzing<span className="blink">_</span>
            </span>
          )}
        </div>

        {/* ID footer */}
        <div className="mt-4 border-t-2 border-[var(--color-edge)] pt-3 flex items-center gap-2">
          <span className="section-label">SESSION ID</span>
          <span className="data-val text-[0.7rem]">{state.investigation_id}</span>
        </div>
      </PixelCard>
    </div>
  )
}
