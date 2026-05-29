import { apiFetch, readApiError, setStoredToken } from './http'
import type { User } from '../types/auth'

interface AuthSessionResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    organization_id: string
  }
  organization: {
    id: string
    name: string
    slug: string
  }
}

interface MeResponse {
  user: AuthSessionResponse['user']
  organization: AuthSessionResponse['organization']
}

function toUser(session: AuthSessionResponse): User {
  return {
    id: session.user.id,
    email: session.user.email,
    orgId: session.organization.slug,
    orgName: session.organization.name,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
}

export async function signupApi(
  email: string,
  password: string,
  orgName: string,
): Promise<User> {
  const response = await apiFetch('/api/v1/auth/signup', {
    method: 'POST',
    body: JSON.stringify({
      organization_name: orgName,
      email,
      password,
      full_name: '',
    }),
  })
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  const session = (await response.json()) as AuthSessionResponse
  setStoredToken(session.access_token)
  return toUser(session)
}

export async function loginApi(email: string, password: string): Promise<User> {
  const response = await apiFetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  const session = (await response.json()) as AuthSessionResponse
  setStoredToken(session.access_token)
  return toUser(session)
}

export async function fetchMeApi(): Promise<User> {
  const response = await apiFetch('/api/v1/auth/me')
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  const me = (await response.json()) as MeResponse
  return {
    id: me.user.id,
    email: me.user.email,
    orgId: me.organization.slug,
    orgName: me.organization.name,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
}

export function logoutApi(): void {
  setStoredToken(null)
}
