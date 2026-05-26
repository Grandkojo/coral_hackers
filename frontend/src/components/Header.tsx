import type { Phase } from '../types/index'
import StatusBadge from './StatusBadge'
import type { BadgeVariant } from './StatusBadge'

const PHASE_STATUS: Record<Phase, { label: string; variant: BadgeVariant }> = {
  idle:          { label: 'ONLINE',         variant: 'online' },
  investigating: { label: 'INVESTIGATING',  variant: 'investigating' },
  complete:      { label: 'RESOLVED',       variant: 'resolved' },
}

interface HeaderProps {
  phase: Phase
}

export default function Header({ phase }: HeaderProps) {
  const status = PHASE_STATUS[phase]
  return (
    <header className="border-b-2 border-[var(--color-edge)] bg-[var(--color-surface)] px-6 py-3">
      <div className="mx-auto flex max-w-4xl items-center justify-between">
        <div className="flex items-center gap-5">
          <span
            className="font-pixel text-[0.7rem] text-[var(--color-accent)]"
            style={{ lineHeight: 1.6 }}
          >
            INVINCIBLE
          </span>
          <span className="hidden font-mono text-[0.6rem] text-[var(--color-muted)] md:block">
            {'// PRODUCTION INCIDENT INTELLIGENCE'}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden font-mono text-[0.55rem] text-[var(--color-muted)] sm:block">
            v0.1.0-alpha
          </span>
          <StatusBadge label={status.label} variant={status.variant} />
        </div>
      </div>
    </header>
  )
}
