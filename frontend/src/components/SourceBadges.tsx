const SOURCES = [
  { name: 'GITHUB',  color: 'var(--color-ink)',    bg: 'rgba(221,232,255,0.05)' },
  { name: 'SENTRY',  color: 'var(--color-danger)', bg: 'rgba(255,68,102,0.06)'  },
  { name: 'SLACK',   color: 'var(--color-cyan)',   bg: 'rgba(0,212,255,0.06)'   },
  { name: 'VERCEL',  color: 'var(--color-ink)',    bg: 'rgba(221,232,255,0.05)' },
] as const

export default function SourceBadges() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      {SOURCES.map((s) => (
        <span
          key={s.name}
          className="source-tag"
          style={{ color: s.color, borderColor: s.color, background: s.bg }}
        >
          <span
            className="status-dot"
            style={{ backgroundColor: s.color, width: '5px', height: '5px' }}
          />
          {s.name}
        </span>
      ))}
    </div>
  )
}
