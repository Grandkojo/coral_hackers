export interface LoginCredentials {
  email: string
  password: string
}

export interface SignupCredentials {
  email: string
  password: string
  confirmPassword: string
  orgName: string
}

export interface OAuthProvider {
  provider: 'google' | 'github'
  clientId: string
  redirectUri: string
}

export interface User {
  id: string
  email: string
  orgId: string
  orgName: string
  createdAt: string
  updatedAt: string
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken: string
}

export interface AuthError {
  code: string
  message: string
  details?: Record<string, unknown>
}
