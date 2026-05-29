import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiEye, FiEyeOff } from 'react-icons/fi'
import { SiGoogle } from 'react-icons/si'
import { useAuth } from '../hooks/useAuth'
import type { LoginCredentials } from '../types/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setCredentials((prev) => ({ ...prev, [name]: value }))
    if (error) setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!credentials.email || !credentials.password) {
      setError('Email and password are required')
      return
    }
    setIsSubmitting(true)
    try {
      const user = await login(credentials.email, credentials.password)
      navigate(`/${user.orgId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGoogleSignIn = () => {
    console.log('Google sign-in clicked')
  }

  return (
    <div className="flex items-center justify-center px-4 md:h-screen">
      <div className="w-full py-8 md:py-0" style={{ maxWidth: '480px' }}>
        <div className="card">
          <div className="card-header">
            <div>
              <h1 className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>
                Sign In
              </h1>
              <p className="text-sm" style={{ color: 'var(--ink-2)' }}>
                Reef — Incident Intelligence
              </p>
            </div>
          </div>

          <div className="p-6 space-y-5">
            {error && (
              <div
                className="p-3 text-sm border"
                style={{
                  background: 'var(--red-dim)',
                  borderColor: 'var(--red)',
                  color: 'var(--red)',
                }}
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="label block">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="field-input"
                  placeholder="you@example.com"
                  value={credentials.email}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="label block">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    className="field-input pr-10"
                    placeholder="••••••••"
                    value={credentials.password}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                    style={{ color: 'var(--muted)' }}
                    tabIndex={-1}
                  >
                    {showPassword ? <FiEyeOff size={18} /> : <FiEye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full text-center justify-center"
                disabled={isSubmitting || !credentials.email || !credentials.password}
              >
                {isSubmitting ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t" style={{ borderColor: 'var(--border)' }} />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2" style={{ background: 'var(--surface)', color: 'var(--muted)' }}>
                  or continue with
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              className="btn btn-secondary w-full text-center justify-center"
              disabled={isSubmitting}
            >
              <SiGoogle size={16} />
              Google
            </button>

            <div className="text-center text-sm" style={{ color: 'var(--ink-2)' }}>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => navigate('/signup')}
                className="font-semibold"
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Sign up
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
