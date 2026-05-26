interface PixelCardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'accent' | 'danger'
  title?: string
  titleRight?: React.ReactNode
}

const CARD_CLASS: Record<NonNullable<PixelCardProps['variant']>, string> = {
  default: 'pixel-card',
  accent: 'pixel-card-accent',
  danger: 'pixel-card-danger',
}

const BORDER_CLASS: Record<NonNullable<PixelCardProps['variant']>, string> = {
  default: 'border-[var(--color-edge)]',
  accent: 'border-[var(--color-accent)]',
  danger: 'border-[var(--color-danger)]',
}

export default function PixelCard({
  children,
  className = '',
  variant = 'default',
  title,
  titleRight,
}: PixelCardProps) {
  return (
    <div className={`${CARD_CLASS[variant]} ${className}`}>
      {title ? (
        <>
          <div
            className={`flex items-center justify-between border-b-2 ${BORDER_CLASS[variant]} px-4 py-2.5`}
          >
            <span className="section-label">{title}</span>
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
