import { apiFetch, readApiError } from './http'

export interface OrganizationProfile {
  organization_id: string
  name: string
  slug: string
  has_github: boolean
  has_sentry: boolean
  has_slack: boolean
  has_vercel: boolean
  github_owner: string
  github_repo: string
  github_account_type: 'user' | 'org'
  sentry_org: string
  slack_incident_channel: string
  coral_ready: boolean
  github_token_hint: string
  sentry_token_hint: string
  slack_token_hint: string
  vercel_token_hint: string
}

export interface OrganizationCredentialsPayload {
  github_token?: string
  github_owner?: string
  github_repo?: string
  github_account_type?: 'user' | 'org'
  sentry_org?: string
  sentry_token?: string
  slack_token?: string
  slack_incident_channel?: string
  vercel_token?: string
}

export async function fetchOrganizationProfile(): Promise<OrganizationProfile> {
  const response = await apiFetch('/api/v1/organizations/me/profile')
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  return response.json() as Promise<OrganizationProfile>
}

export async function updateOrganizationCredentials(
  payload: OrganizationCredentialsPayload,
): Promise<{ profile: OrganizationProfile; coral_ready: boolean; message: string }> {
  const response = await apiFetch('/api/v1/organizations/me/credentials', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  return response.json() as Promise<{
    profile: OrganizationProfile
    coral_ready: boolean
    message: string
  }>
}
