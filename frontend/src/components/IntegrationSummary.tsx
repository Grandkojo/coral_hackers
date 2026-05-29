import type { OrganizationProfile } from '../api/organizations'

interface IntegrationSummaryProps {
  profile: OrganizationProfile
}

function StatusLine({
  label,
  detail,
  ok,
}: {
  label: string
  detail: string
  ok: boolean
}) {
  return (
    <li className={`integration-summary-item ${ok ? 'integration-summary-item--ok' : ''}`}>
      <span className="integration-summary-dot" aria-hidden="true" />
      <span>
        <strong>{label}</strong>
        <span className="integration-summary-detail">{detail}</span>
      </span>
    </li>
  )
}

export default function IntegrationSummary({ profile }: IntegrationSummaryProps) {
  const githubDetail = profile.has_github
    ? `${profile.github_owner}/${profile.github_repo}${profile.github_token_hint ? ` · ${profile.github_token_hint}` : ''}`
    : 'Not configured'

  const sentryDetail = profile.has_sentry
    ? `${profile.sentry_org}${profile.sentry_token_hint ? ` · ${profile.sentry_token_hint}` : ''}`
    : profile.sentry_org
      ? `${profile.sentry_org} (token missing)`
      : 'Not configured'

  const slackDetail = profile.has_slack
    ? `#${profile.slack_incident_channel}${profile.slack_token_hint ? ` · ${profile.slack_token_hint}` : ''}`
    : profile.slack_incident_channel
      ? `#${profile.slack_incident_channel} (token missing)`
      : 'Not configured'

  const vercelDetail = profile.has_vercel
    ? profile.vercel_token_hint || 'Token saved'
    : 'Not configured'

  return (
    <div className="integration-summary">
      <h2 className="integration-summary-title">Saved configuration</h2>
      <ul className="integration-summary-list">
        <StatusLine label="GitHub" detail={githubDetail} ok={profile.has_github} />
        <StatusLine label="Sentry" detail={sentryDetail} ok={profile.has_sentry} />
        <StatusLine label="Slack" detail={slackDetail} ok={profile.has_slack} />
        <StatusLine label="Vercel" detail={vercelDetail} ok={profile.has_vercel} />
      </ul>
    </div>
  )
}
