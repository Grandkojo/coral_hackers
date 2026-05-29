import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  fetchOrganizationProfile,
  updateOrganizationCredentials,
  type OrganizationProfile,
} from '../api/organizations'
import IntegrationCredentialField from '../components/IntegrationCredentialField'
import IntegrationSummary from '../components/IntegrationSummary'
import { useAuth } from '../hooks/useAuth'

export default function ProfilePage() {
  const { orgId } = useParams<{ orgId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [profile, setProfile] = useState<OrganizationProfile | null>(null)
  const [githubToken, setGithubToken] = useState('')
  const [githubOwner, setGithubOwner] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [githubAccountType, setGithubAccountType] = useState<'user' | 'org'>('org')
  const [sentryOrg, setSentryOrg] = useState('')
  const [sentryToken, setSentryToken] = useState('')
  const [slackToken, setSlackToken] = useState('')
  const [slackChannel, setSlackChannel] = useState('incidents')
  const [vercelToken, setVercelToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  function applyProfile(loaded: OrganizationProfile) {
    setProfile(loaded)
    setGithubOwner(loaded.github_owner)
    setGithubRepo(loaded.github_repo)
    setGithubAccountType(loaded.github_account_type)
    setSentryOrg(loaded.sentry_org)
    setSlackChannel(loaded.slack_incident_channel || 'incidents')
  }

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      navigate('/login', { replace: true })
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const loaded = await fetchOrganizationProfile()
        if (cancelled) return
        applyProfile(loaded)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load profile')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [authLoading, isAuthenticated, navigate])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setIsSaving(true)
    try {
      const result = await updateOrganizationCredentials({
        github_token: githubToken || undefined,
        github_owner: githubOwner || undefined,
        github_repo: githubRepo || undefined,
        github_account_type: githubAccountType,
        sentry_org: sentryOrg || undefined,
        sentry_token: sentryToken || undefined,
        slack_token: slackToken || undefined,
        slack_incident_channel: slackChannel || undefined,
        vercel_token: vercelToken || undefined,
      })
      applyProfile(result.profile)
      setSuccess(result.message)
      setGithubToken('')
      setSentryToken('')
      setSlackToken('')
      setVercelToken('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save credentials')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <div className="card p-6">Loading integrations…</div>
  }

  if (!profile) {
    return <div className="card p-6">Could not load organization profile.</div>
  }

  return (
    <div className="profile-layout fade-up">
      <div className="card">
        <div className="card-header flex items-start justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>
              Organization integrations
            </h1>
            <p className="text-sm" style={{ color: 'var(--ink-2)' }}>
              {profile.name} — Reef uses these credentials for Coral queries on your
              GitHub, Sentry, Slack, and Vercel data.
            </p>
          </div>
          {profile.coral_ready ? (
            <span className="status-pill status-pill--ok">Coral ready</span>
          ) : (
            <span className="status-pill status-pill--warn">Setup required</span>
          )}
        </div>

        <div className="px-6 pb-2">
          <IntegrationSummary profile={profile} />
        </div>

        <form className="p-6 space-y-6 border-t" style={{ borderColor: 'var(--border)' }} onSubmit={(e) => void handleSave(e)}>
          <section className="space-y-3">
            <h2 className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
              GitHub
            </h2>
            <IntegrationCredentialField
              id="gh-token"
              label="Fine-grained PAT"
              value={githubToken}
              onChange={setGithubToken}
              configured={Boolean(profile.github_token_hint || profile.has_github)}
              hint={profile.github_token_hint}
              placeholder="github_pat_..."
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="label block" htmlFor="gh-owner">
                  Owner / org slug
                </label>
                <input
                  id="gh-owner"
                  className="field-input"
                  value={githubOwner}
                  onChange={(e) => setGithubOwner(e.target.value)}
                />
              </div>
              <div>
                <label className="label block" htmlFor="gh-repo">
                  Repository
                </label>
                <input
                  id="gh-repo"
                  className="field-input"
                  value={githubRepo}
                  onChange={(e) => setGithubRepo(e.target.value)}
                />
              </div>
            </div>
            <label className="label block" htmlFor="gh-type">
              Account type
            </label>
            <select
              id="gh-type"
              className="field-input"
              value={githubAccountType}
              onChange={(e) => setGithubAccountType(e.target.value as 'user' | 'org')}
            >
              <option value="org">Organization</option>
              <option value="user">Personal</option>
            </select>
          </section>

          <section className="space-y-3 border-t pt-6" style={{ borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
              Sentry
            </h2>
            <label className="label block" htmlFor="sentry-org">
              Organization slug
            </label>
            <input
              id="sentry-org"
              className="field-input"
              value={sentryOrg}
              onChange={(e) => setSentryOrg(e.target.value)}
            />
            <IntegrationCredentialField
              id="sentry-token"
              label="Auth token"
              value={sentryToken}
              onChange={setSentryToken}
              configured={Boolean(profile.sentry_token_hint)}
              hint={profile.sentry_token_hint}
              placeholder="sntrys_..."
            />
          </section>

          <section className="space-y-3 border-t pt-6" style={{ borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
              Slack
            </h2>
            <IntegrationCredentialField
              id="slack-token"
              label="Bot token"
              value={slackToken}
              onChange={setSlackToken}
              configured={profile.has_slack}
              hint={profile.slack_token_hint}
              placeholder="xoxb-..."
            />
            <label className="label block" htmlFor="slack-channel">
              Incident channel
            </label>
            <input
              id="slack-channel"
              className="field-input"
              value={slackChannel}
              onChange={(e) => setSlackChannel(e.target.value)}
            />
          </section>

          <section className="space-y-3 border-t pt-6" style={{ borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>
              Vercel
            </h2>
            <IntegrationCredentialField
              id="vercel-token"
              label="API token"
              value={vercelToken}
              onChange={setVercelToken}
              configured={profile.has_vercel}
              hint={profile.vercel_token_hint}
            />
          </section>

          {error ? (
            <div className="p-3 text-sm border" style={{ background: 'var(--red-dim)', borderColor: 'var(--red)', color: 'var(--red)' }}>
              {error}
            </div>
          ) : null}
          {success ? (
            <div className="p-3 text-sm border alert-banner--success">{success}</div>
          ) : null}

          <div className="flex flex-wrap gap-3">
            <button type="submit" className="btn btn-primary" disabled={isSaving}>
              {isSaving ? 'Saving & configuring Coral…' : 'Save integrations'}
            </button>
            {orgId ? (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => navigate(`/${orgId}`)}
              >
                Back to dashboard
              </button>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  )
}
