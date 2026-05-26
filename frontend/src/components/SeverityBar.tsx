interface SeverityBarProps {
  score: number
}

function getSeverityColor(score: number): string {
  if (score >= 0.7) return 'var(--color-danger)'
  if (score >= 0.4) return 'var(--color-warning)'
  return 'var(--color-accent)'
}

function getSeverityLabel(score: number): string {
  if (score >= 0.7) return 'CRITICAL'
  if (score >= 0.4) return 'MODERATE'
  return 'LOW'
}

export default function SeverityBar({ score }: SeverityBarProps) {
  const color = getSeverityColor(score)
  const label = getSeverityLabel(score)
  const pct = Math.round(score * 100)

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="section-label">SEVERITY SCORE</span>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.65rem] font-semibold" style={{ color }}>
            {label}
          </span>
          <span className="data-val text-sm font-bold">{score.toFixed(2)}</span>
        </div>
      </div>
      <div className="severity-bar-track">
        <div
          className="severity-bar-fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
