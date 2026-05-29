interface GithubBudgetHintProps {
  used: number
  max: number
  rateLimited?: boolean
  /** Pre-run note on the launch form (no usage counts yet). */
  variant?: 'form' | 'report'
}

export default function GithubBudgetHint({
  used,
  max,
  rateLimited = false,
  variant = 'report',
}: GithubBudgetHintProps) {
  const atCap = used >= max && max > 0
  const label =
    variant === 'form'
      ? `GitHub API budget: up to ${max} Coral queries per investigation (Sentry/Vercel unaffected).`
      : rateLimited
        ? `GitHub API rate limited — used ${used}/${max} before skip`
        : atCap
          ? `GitHub queries: ${used}/${max} (cap reached)`
          : `GitHub queries: ${used}/${max}`

  return (
    <p
      className={`github-budget-hint github-budget-hint--${variant}${
        rateLimited ? ' github-budget-hint--limited' : ''
      }${atCap && !rateLimited ? ' github-budget-hint--cap' : ''}`}
      role={rateLimited ? 'alert' : 'status'}
    >
      {label}
    </p>
  )
}
