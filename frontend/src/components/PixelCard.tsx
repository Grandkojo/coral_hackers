interface PixelCardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'accent' | 'danger'
  title?: string
  titleRight?: React.ReactNode
  hoverable?: boolean
}

const CARD_CLASS: Record<NonNullable<PixelCardProps['variant']>, string> = {
  default: 'card',
  accent:  'card-accent',
  danger:  'card-danger',
}

// Reusable card container with optional section header and title bar
export default function PixelCard({
  children,
  className = '',
  variant = 'default',
  title,
  titleRight,
  hoverable = false,
}: PixelCardProps) {
  const hoverClass = hoverable ? 'card-hover' : ''

  return (
    <div className={`${CARD_CLASS[variant]} ${hoverClass} ${className}`}>
      {title ? (
        <>
          <div className="card-header">
            <span className="label">{title}</span>
            {titleRight ? titleRight : null}
          </div>
          <div className="p-5">{children}</div>
        </>
      ) : (
        children
      )}
    </div>
  )
}
