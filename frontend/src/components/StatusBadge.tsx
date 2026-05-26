export type BadgeVariant =
  | 'online'
  | 'investigating'
  | 'resolved'
  | 'autonomous'
  | 'human-paired'
  | 'danger'

interface StatusBadgeProps {
  label: string
  variant: BadgeVariant
}

const BADGE_STYLES: Record<BadgeVariant, { border: string; text: string; dot: string; pulse: string }> = {
  online:        { border: 'var(--color-accent)',  text: 'var(--color-accent)',  dot: 'var(--color-accent)',  pulse: 'pulse-green' },
  investigating: { border: 'var(--color-warning)', text: 'var(--color-warning)', dot: 'var(--color-warning)', pulse: 'pulse-amber' },
  resolved:      { border: 'var(--color-cyan)',    text: 'var(--color-cyan)',    dot: 'var(--color-cyan)',    pulse: 'pulse-green' },
  autonomous:    { border: 'var(--color-accent)',  text: 'var(--color-accent)',  dot: 'var(--color-accent)',  pulse: 'pulse-green' },
  'human-paired':{ border: 'var(--color-warning)', text: 'var(--color-warning)', dot: 'var(--color-warning)', pulse: 'pulse-amber' },
  danger:        { border: 'var(--color-danger)',  text: 'var(--color-danger)',  dot: 'var(--color-danger)',  pulse: 'pulse-amber' },
}

export default function StatusBadge({ label, variant }: StatusBadgeProps) {
  const s = BADGE_STYLES[variant]
  return (
    <span
      className="inline-flex items-center gap-1.5 border px-2 py-0.5 font-mono text-[0.58rem] font-semibold uppercase tracking-widest"
      style={{ borderColor: s.border, color: s.text }}
    >
      <span
        className={`status-dot ${s.pulse}`}
        style={{ backgroundColor: s.dot }}
      />
      {label}
    </span>
  )
}
