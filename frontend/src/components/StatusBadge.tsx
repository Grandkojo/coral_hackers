export type BadgeVariant =
  | 'online'
  | 'investigating'
  | 'resolved'
  | 'autonomous'
  | 'human-paired'
  | 'critical'

interface StatusBadgeProps {
  label: string
  variant: BadgeVariant
}

const STYLES: Record<BadgeVariant, { color: string; dot: string; pulse: string }> = {
  online:         { color: 'var(--green)',  dot: 'var(--green)',  pulse: 'pulse-green' },
  investigating:  { color: 'var(--amber)',  dot: 'var(--amber)',  pulse: 'pulse-amber' },
  resolved:       { color: 'var(--blue)',   dot: 'var(--blue)',   pulse: 'pulse-green' },
  autonomous:     { color: 'var(--green)',  dot: 'var(--green)',  pulse: 'pulse-green' },
  'human-paired': { color: 'var(--amber)',  dot: 'var(--amber)',  pulse: 'pulse-amber' },
  critical:       { color: 'var(--red)',    dot: 'var(--red)',    pulse: 'pulse-amber' },
}

// Inline status indicator with monospace label
export default function StatusBadge({ label, variant }: StatusBadgeProps) {
  const s = STYLES[variant]
  return (
    <span
      className="badge"
      style={{ color: s.color, borderColor: s.color, background: 'transparent' }}
    >
      {label}
    </span>
  )
}
