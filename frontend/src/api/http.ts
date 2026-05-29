const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const TOKEN_KEY = 'reef_access_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getStoredToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(`${API_BASE}${path}`, { ...init, headers })
}

export async function readApiError(response: Response): Promise<string> {
  const text = await response.text()
  if (!text) {
    return `Request failed (${response.status})`
  }
  try {
    const json = JSON.parse(text) as { detail?: string | { msg?: string }[] }
    if (typeof json.detail === 'string') {
      return json.detail
    }
    if (Array.isArray(json.detail) && json.detail[0]?.msg) {
      return json.detail[0].msg
    }
  } catch {
    /* plain text */
  }
  return text
}
