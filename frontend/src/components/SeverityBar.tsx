interface SeverityBarProps {
  score: number
}

// Derives color and label directly in render — no effect needed
function getSeverityMeta(score: number): { color: string; label: string; dimColor: string } {
  if (score >= 0.7) return { color: 'var(--red)',   label: 'Critical', dimColor: 'var(--red-dim)'   }
  if (score >= 0.4) return { color: 'var(--amber)', label: 'Moderate', dimColor: 'var(--amber-dim)' }
  return              { color: 'var(--green)', label: 'Low',      dimColor: 'var(--green-dim)' }
}

// Animated severity fill bar with derived color coding
export default function SeverityBar({ score }: SeverityBarProps) {
  const meta = getSeverityMeta(score)
  const pct  = Math.round(score * 100)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="label">Severity Score</span>
        <div className="flex items-center gap-3">
          <span
            className="font-mono text-[0.65rem] font-bold"
            style={{ color: meta.color }}
          >
            {meta.label}
          </span>
          <span
            className="font-mono text-sm font-bold"
            style={{ color: meta.color }}
          >
            {score.toFixed(2)}
          </span>
        </div>
      </div>
      <div className="severity-track">
        <div
          className="severity-fill"
          style={{ width: `${pct}%`, backgroundColor: meta.color }}
        />
      </div>
      <p className="font-mono text-[0.6rem]" style={{ color: 'var(--muted)' }}>
        {pct}% — {score >= 0.7 ? 'human approval required before remediation' : 'agent may proceed autonomously'}
      </p>
    </div>
  )
}
